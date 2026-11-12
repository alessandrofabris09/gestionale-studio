from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.timezone import localdate

from clienti.models import Cliente
from immobili.models import Immobile
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
