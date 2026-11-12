from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.timezone import localdate

from clienti.models import Cliente
from immobili.models import Immobile
from parcelle.models import Parcella
from pratiche.models import Pratica
from scadenze.models import Scadenza
from studi.models import Studio, ProfiloUtente


class BackupUnificatoTests(TestCase):
    def test_vecchio_indirizzo_apre_backup_principale(self):
        user = User.objects.create_superuser('qa_backup', '', 'Solo-qa-829!')
        self.client.force_login(user)
        with patch('backups.views.esegui_backup_database') as backup:
            for method in [self.client.get, self.client.post]:
                response = method('/dashboard/backup/')
                self.assertRedirects(response, '/backups/', fetch_redirect_response=False)
            backup.assert_not_called()

    def test_titolare_non_accede_backup_storico(self):
        user = User.objects.create_user('qa_owner_backup')
        studio = Studio.objects.create(nome='QA', titolare=user)
        ProfiloUtente.objects.create(user=user, studio=studio, ruolo='TITOLARE')
        self.client.force_login(user)
        self.assertEqual(self.client.get('/dashboard/backup/').status_code, 403)


class PraticheOperativeTests(TestCase):
    def test_invito_prima_pratica_rispetta_studio_ruolo_e_limite(self):
        titolare = User.objects.create_user('qa_prima_pratica')
        studio = Studio.objects.create(nome='QA primo studio', titolare=titolare, stato_abbonamento='ATTIVO')
        profilo = ProfiloUtente.objects.create(user=titolare, studio=studio, ruolo='TITOLARE')
        altro_titolare = User.objects.create_user('qa_prima_pratica_altro')
        altro_studio = Studio.objects.create(nome='QA altro studio', titolare=altro_titolare)

        def crea_pratica_conclusa(studio):
            cliente = Cliente.objects.create(nome='Cliente QA', studio=studio)
            immobile = Immobile.objects.create(cliente=cliente, comune='QA', studio=studio)
            Pratica.objects.create(
                oggetto='Pratica QA', studio=studio, cliente=cliente, immobile=immobile,
                comune='QA', tipo_pratica='CILA', stato='CONCLUSA',
            )

        crea_pratica_conclusa(altro_studio)
        self.client.force_login(titolare)
        dashboard = reverse('home')
        invito = 'Crea la prima pratica'
        pagina = self.client.get(dashboard)
        self.assertContains(pagina, invito)
        self.assertContains(pagina, f'href="{reverse("nuova_pratica")}"')
        self.assertEqual(self.client.get(reverse('nuova_pratica')).status_code, 200)

        profilo.ruolo = 'SEGRETERIA'
        profilo.save(update_fields=['ruolo'])
        self.assertNotContains(self.client.get(dashboard), invito)
        profilo.ruolo = 'TITOLARE'
        profilo.save(update_fields=['ruolo'])

        limite_iniziale = studio.limite_pratiche
        studio.limite_pratiche = 0
        studio.save(update_fields=['limite_pratiche'])
        self.assertNotContains(self.client.get(dashboard), invito)
        studio.limite_pratiche = limite_iniziale
        studio.save(update_fields=['limite_pratiche'])

        crea_pratica_conclusa(studio)
        self.assertNotContains(self.client.get(dashboard), invito)

    def test_ordine_scadenze_priorita_paginazione_e_isolamento(self):
        titolare = User.objects.create_user('qa_dashboard_operativa')
        studio = Studio.objects.create(nome='QA operativo', titolare=titolare, stato_abbonamento='ATTIVO')
        ProfiloUtente.objects.create(user=titolare, studio=studio, ruolo='TITOLARE')
        altro_titolare = User.objects.create_user('qa_dashboard_altro')
        altro_studio = Studio.objects.create(nome='QA altro', titolare=altro_titolare)

        def pratica(oggetto, studio=studio, stato='IN_CORSO'):
            cliente = Cliente.objects.create(nome=oggetto, studio=studio)
            immobile = Immobile.objects.create(cliente=cliente, comune='QA', studio=studio)
            return Pratica.objects.create(
                oggetto=oggetto, studio=studio, cliente=cliente, immobile=immobile,
                comune='QA', tipo_pratica='CILA', stato=stato,
            )

        bassa = pratica('QA priorità bassa')
        alta = pratica('QA priorità alta')
        scaduta = pratica('QA scaduta')
        senza_data = pratica('QA senza data')
        chiusa = pratica('QA chiusa', stato='CONCLUSA')
        altrui = pratica('QA riservata', studio=altro_studio)
        oggi = localdate()
        ieri = oggi - timedelta(days=1)
        for p, data, priorita in (
            (bassa, oggi, 'BASSA'), (alta, oggi, 'ALTA'),
            (alta, oggi, 'MEDIA'), (scaduta, ieri, 'BASSA'),
            (chiusa, ieri, 'ALTA'), (altrui, ieri, 'ALTA'),
        ):
            Scadenza.objects.create(pratica=p, titolo='QA', data_scadenza=data, priorita=priorita)
        Scadenza.objects.create(
            pratica=senza_data, titolo='QA completata', data_scadenza=ieri, completata=True,
        )
        Scadenza.objects.create(
            pratica=senza_data, titolo='QA archiviata', data_scadenza=ieri, archiviata=True,
        )
        altre = [pratica(f'QA senza data {n}') for n in range(9)]
        self.client.force_login(titolare)

        pagina = self.client.get(reverse('home'))
        operative = pagina.context['pratiche_operative']
        self.assertEqual(operative.paginator.count, 13)
        self.assertEqual(list(operative)[:4], [scaduta, alta, bassa, senza_data])
        self.assertIsNone(operative[3].scadenza_operativa)
        self.assertContains(pagina, reverse('dettaglio_pratica', args=[alta.pk]))
        self.assertContains(pagina, '?operative=2#notifiche-operative')
        self.assertNotContains(pagina, altrui.oggetto)
        seconda = self.client.get(reverse('home'), {'operative': 2})
        self.assertEqual(list(seconda.context['pratiche_operative']), [altre[-1]])


class RiepilogoIncassiTests(TestCase):
    def test_cila_dalle_ore_all_acconto(self):
        titolare = User.objects.create_user('qa_incassi_cila')
        studio = Studio.objects.create(nome='Studio CILA', titolare=titolare, stato_abbonamento='ATTIVO')
        ProfiloUtente.objects.create(user=titolare, studio=studio, ruolo='TITOLARE')
        cliente = Cliente.objects.create(nome='Cliente CILA', studio=studio)
        immobile = Immobile.objects.create(cliente=cliente, comune='Treviso', studio=studio)
        pratica = Pratica.objects.create(
            oggetto='CILA di collaudo', studio=studio, cliente=cliente, immobile=immobile,
            comune='Treviso', tipo_pratica='CILA',
        )
        self.client.force_login(titolare)
        oggi = localdate()
        consuntivo = reverse('lista_ore_pratica', args=[pratica.pk])
        for attivita, ore in [('SOPRALLUOGO', '2'), ('RILIEVO', '3')]:
            risposta = self.client.post(reverse('nuova_voce_ora', args=[pratica.pk]), {
                'data': oggi.isoformat(), 'tipo_attivita': attivita, 'descrizione': attivita,
                'ore': ore, 'tariffa_oraria': '40', 'fatturabile': 'on',
            })
            self.assertRedirects(risposta, consuntivo)

        risposta = self.client.post(reverse('genera_parcella_da_ore', args=[pratica.pk]))
        parcella = pratica.parcelle.get()
        self.assertRedirects(risposta, reverse('modifica_parcella', args=[parcella.pk]))
        self.assertEqual(parcella.importo, Decimal('200.00'))
        self.assertEqual(pratica.voci_ore.filter(parcella=parcella).count(), 2)
        parcella.data_scadenza = oggi - timedelta(days=1)
        parcella.save(update_fields=['data_scadenza'])
        Parcella.objects.create(
            pratica=pratica, tipo_documento='PREVENTIVO', descrizione='Preventivo QA', importo=Decimal('500.00'),
            data_scadenza=oggi - timedelta(days=1),
        )

        storico = reverse('storico_incassi', args=[parcella.pk])
        chiave = self.client.get(storico).context['form'].initial['chiave']
        acconto = {
            'chiave': chiave, 'importo': '100.00', 'data': oggi.isoformat(), 'riferimento': 'Acconto',
        }
        for _ in range(2):
            self.assertRedirects(self.client.post(storico, acconto), storico)
        parcella.refresh_from_db()
        self.assertEqual(parcella.stato, 'PARZIALE')
        self.assertEqual(parcella.incassi.count(), 1)
        self.assertEqual(parcella.saldo_residuo, Decimal('156.20'))
        self.assertEqual(self.client.get(storico).context['parcella'].saldo_residuo, Decimal('156.20'))
        scheda = self.client.get(reverse('dettaglio_pratica', args=[pratica.pk]))
        self.assertContains(scheda, 'Da incassare: € 156,20')
        self.assertContains(scheda, f'href="{storico}"')
        dashboard = self.client.get(reverse('home')).context
        self.assertEqual(dashboard['totale_parcelle'], Decimal('256.20'))
        self.assertEqual(dashboard['totale_incassato'], Decimal('100.00'))
        self.assertEqual(dashboard['totale_da_incassare'], Decimal('156.20'))
        self.assertEqual(dashboard['parcelle_scadute'], 1)

        chiave_saldo = self.client.get(storico).context['form'].initial['chiave']
        self.assertRedirects(self.client.post(storico, {
            'chiave': chiave_saldo, 'importo': '156.20', 'data': oggi.isoformat(), 'riferimento': 'Saldo',
        }), storico)
        parcella.refresh_from_db()
        self.assertEqual(parcella.stato, 'PAGATO')
        self.assertEqual(parcella.saldo_residuo, Decimal('0.00'))
        self.assertEqual(parcella.incassi.count(), 2)
        self.assertIsNone(self.client.get(storico).context['form'])
        dashboard = self.client.get(reverse('home')).context
        self.assertEqual(dashboard['totale_incassato'], Decimal('256.20'))
        self.assertEqual(dashboard['totale_da_incassare'], Decimal('0.00'))
        self.assertEqual(dashboard['parcelle_scadute'], 0)
