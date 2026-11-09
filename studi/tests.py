from datetime import date
from django.contrib.auth.models import User
from django.test import TestCase, Client, RequestFactory
from studi.models import Studio, ProfiloUtente
from studi.utils import get_studio_utente, is_admin_piattaforma
from clienti.models import Cliente
from agenda.models import EventoAgenda


class VerificaFunzionale(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser('qa_admin', 'qa@example.test', 'Solo-test-9382!')
        cls.a = User.objects.create_user('qa_a', password='Solo-test-9382!')
        cls.b = User.objects.create_user('qa_b')
        cls.sa = Studio.objects.create(nome='QA Studio Alfa', titolare=cls.a, stato_abbonamento='ATTIVO')
        cls.sb = Studio.objects.create(nome='QA Studio Beta', titolare=cls.b, stato_abbonamento='ATTIVO')
        ProfiloUtente.objects.create(user=cls.a, studio=cls.sa, ruolo='TITOLARE')
        ProfiloUtente.objects.create(user=cls.b, studio=cls.sb, ruolo='TITOLARE')
        cls.ca = Cliente.objects.create(studio=cls.sa, nome='QA Cliente Alfa')
        cls.cb = Cliente.objects.create(studio=cls.sb, nome='QA Cliente Beta')
        cls.ea = EventoAgenda.objects.create(studio=cls.sa, titolo='QA Evento Alfa', data=date.today())
        cls.eb = EventoAgenda.objects.create(studio=cls.sb, titolo='QA Evento Beta', data=date.today())

    def test_login_e_logout(self):
        self.assertEqual(self.client.get('/dashboard/').status_code, 302)
        self.assertFalse(self.client.login(username='qa_a', password='errata'))
        self.assertTrue(self.client.login(username='qa_a', password='Solo-test-9382!'))
        self.assertEqual(self.client.get('/dashboard/').status_code, 200)
        self.client.post('/logout/')
        self.assertEqual(self.client.get('/dashboard/').status_code, 302)

    def test_admin_dashboard_senza_profilo(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get('/dashboard/').status_code, 200)
        request = RequestFactory().get('/')
        request.user = self.admin
        self.assertIsNone(get_studio_utente(request))
        self.assertTrue(is_admin_piattaforma(request))
        self.assertFalse(ProfiloUtente.objects.filter(user=self.admin).exists())

    def test_pagine_principali_admin_e_titolare(self):
        for user in [self.admin, self.a]:
            self.client.force_login(user)
            for path in ['/dashboard/', '/clienti/', '/immobili/', '/pratiche/', '/documenti/', '/parcelle/', '/agenda/', '/scadenze/', '/utenti/']:
                with self.subTest(user=user.username, path=path):
                    self.assertEqual(self.client.get(path).status_code, 200)

    def test_liste_clienti_bidirezionali(self):
        for user, own, other in [(self.a, self.ca, self.cb), (self.b, self.cb, self.ca)]:
            self.client.force_login(user)
            response = self.client.get('/clienti/')
            self.assertContains(response, own.nome)
            self.assertNotContains(response, other.nome)

    def test_accesso_diretto_cliente_altrui(self):
        self.client.force_login(self.a)
        for path in [f'/clienti/{self.cb.pk}/', f'/clienti/{self.cb.pk}/modifica/', f'/clienti/{self.cb.pk}/elimina/']:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)
                self.assertEqual(self.client.post(path, {'nome': 'Manomesso'}).status_code, 404)
        self.cb.refresh_from_db()
        self.assertEqual(self.cb.nome, 'QA Cliente Beta')

    def test_creazione_cliente_forza_studio_del_titolare(self):
        self.client.force_login(self.a)
        response = self.client.post('/clienti/nuovo/', {'nome': 'QA Nuovo', 'studio': self.sb.pk})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Cliente.objects.get(nome='QA Nuovo').studio_id, self.sa.pk)

    def test_admin_non_crea_senza_studio(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get('/clienti/nuovo/').status_code, 403)
        self.assertEqual(self.client.post('/clienti/nuovo/', {'nome': 'QA Orfano'}).status_code, 403)
        self.assertFalse(Cliente.objects.filter(nome='QA Orfano').exists())

    def test_agenda_e_accesso_diretto_evento_altrui(self):
        self.client.force_login(self.a)
        response = self.client.get('/agenda/')
        self.assertContains(response, self.ea.titolo)
        self.assertNotContains(response, self.eb.titolo)
        for suffix in ['modifica/', 'elimina/', 'completa/']:
            self.assertEqual(self.client.post(f'/agenda/{self.eb.pk}/{suffix}').status_code, 404)
        self.assertTrue(EventoAgenda.objects.filter(pk=self.eb.pk).exists())

    def test_collaboratore_limitato(self):
        user = User.objects.create_user('qa_collaboratore')
        ProfiloUtente.objects.create(user=user, studio=self.sa, ruolo='COLLABORATORE')
        self.client.force_login(user)
        self.assertEqual(self.client.get('/agenda/').status_code, 200)
        for path in ['/clienti/', '/utenti/', '/parcelle/', '/documenti/', '/backups/']:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 403)

    def test_backup_negato_al_titolare(self):
        self.client.force_login(self.a)
        self.assertEqual(self.client.get('/backups/').status_code, 403)

    def test_superuser_con_studio_nel_gestionale(self):
        self.a.is_superuser = True
        self.a.is_staff = True
        self.a.save()
        self.client.force_login(self.a)
        response = self.client.get('/clienti/')
        self.assertNotContains(response, self.cb.nome)
        self.assertEqual(self.client.get(f'/clienti/{self.cb.pk}/').status_code, 404)
        self.assertEqual(self.client.get('/backups/').status_code, 403)

    def test_superuser_con_studio_non_accede_admin_altro_studio(self):
        self.a.is_superuser = True
        self.a.is_staff = True
        self.a.save()
        self.client.force_login(self.a)
        response = self.client.get(f'/admin/studi/studio/{self.sb.pk}/change/')
        self.assertIn(response.status_code, [302, 403, 404], 'Il superuser associato a uno studio accede allo studio altrui tramite /admin/.')

    def test_csrf_rifiuta_post_senza_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.a)
        self.assertEqual(client.post('/clienti/nuovo/', {'nome': 'QA CSRF'}).status_code, 403)

    def test_admin_globale_accede_pannello(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get('/admin/').status_code, 200)
        self.assertEqual(self.client.get(f'/admin/studi/studio/{self.sb.pk}/change/').status_code, 200)

    def test_staff_studio_non_accede_pannello(self):
        self.a.is_staff = True
        self.a.save()
        self.client.force_login(self.a)
        self.assertEqual(self.client.get('/admin/').status_code, 302)

    def test_admin_studio_post_bloccato(self):
        self.a.is_superuser = True
        self.a.is_staff = True
        self.a.save()
        self.client.force_login(self.a)
        response = self.client.post(f'/admin/studi/studio/{self.sb.pk}/change/', {'nome': 'Modificato abusivamente'})
        self.assertEqual(response.status_code, 302)
        self.sb.refresh_from_db()
        self.assertEqual(self.sb.nome, 'QA Studio Beta')

    def test_admin_inattivo_rifiutato(self):
        from django.contrib import admin
        self.admin.is_active = False
        request = RequestFactory().get('/admin/')
        request.user = self.admin
        self.assertFalse(admin.site.has_permission(request))

class VerificaWorkflowEOre(TestCase):
    @classmethod
    def setUpTestData(cls):
        VerificaFunzionale.setUpTestData.__func__(cls)
        from immobili.models import Immobile
        from pratiche.models import Pratica
        from workflow.models import WorkflowPratica, FasePratica, ChecklistPratica, TipoWorkflow
        cls.ia = Immobile.objects.create(studio=cls.sa, cliente=cls.ca, comune='Alfa')
        cls.ib = Immobile.objects.create(studio=cls.sb, cliente=cls.cb, comune='Beta')
        cls.pa = Pratica.objects.create(studio=cls.sa, cliente=cls.ca, immobile=cls.ia, tipo_pratica='CILA', oggetto='QA Alfa', comune='Alfa')
        cls.pb = Pratica.objects.create(studio=cls.sb, cliente=cls.cb, immobile=cls.ib, tipo_pratica='CILA', oggetto='QA Beta', comune='Beta')
        cls.wa = WorkflowPratica.objects.create(pratica=cls.pa, workflow=TipoWorkflow.objects.create(nome='QA workflow'))
        cls.wb = WorkflowPratica.objects.create(pratica=cls.pb)
        cls.fase = FasePratica.objects.create(workflow_pratica=cls.wa, titolo='QA fase')
        cls.voce = ChecklistPratica.objects.create(workflow_pratica=cls.wa, voce='QA voce')

    def test_workflow_get_non_modifica(self):
        self.client.force_login(self.a)
        for path in [f'/workflow/fase/{self.fase.pk}/toggle/', f'/workflow/checklist/{self.voce.pk}/toggle/']:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 405)
        self.fase.refresh_from_db()
        self.voce.refresh_from_db()
        self.assertFalse(self.fase.completata)
        self.assertFalse(self.voce.completato)

    def test_workflow_post_valido_e_csrf(self):
        from workflow.models import FasePratica
        other = FasePratica.objects.create(workflow_pratica=self.wb, titolo='Altrui')
        self.client.force_login(self.a)
        self.assertEqual(self.client.post(f'/workflow/fase/{other.pk}/toggle/').status_code, 404)
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.a)
        self.assertEqual(strict.post(f'/workflow/fase/{self.fase.pk}/toggle/').status_code, 403)
        for path in [f'/workflow/fase/{self.fase.pk}/toggle/', f'/workflow/checklist/{self.voce.pk}/toggle/']:
            self.assertEqual(self.client.post(path).status_code, 302)
        self.fase.refresh_from_db()
        self.voce.refresh_from_db()
        self.assertTrue(self.fase.completata)
        self.assertTrue(self.voce.completato)
        response = self.client.get(f'/pratiche/{self.pa.pk}/')
        self.assertContains(response, f'action="/workflow/fase/{self.fase.pk}/toggle/"')
        self.assertContains(response, f'action="/workflow/checklist/{self.voce.pk}/toggle/"')

    def test_backup_get_non_esegue_backup(self):
        from unittest.mock import patch
        self.client.force_login(self.admin)
        with patch('backups.views.esegui_backup_database') as backup:
            self.assertEqual(self.client.get('/backups/crea/').status_code, 405)
            backup.assert_not_called()
            self.assertEqual(self.client.post('/backups/crea/').status_code, 302)
            backup.assert_called_once()
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.admin)
        self.assertEqual(strict.post('/backups/crea/').status_code, 403)

    def test_incassi_multipli_con_importo_storico_e_reinvio(self):
        from decimal import Decimal
        from uuid import uuid4
        from django.urls import reverse
        from parcelle.models import Parcella

        parcella = Parcella.objects.create(
            pratica=self.pa, descrizione='Prova incassi', importo=Decimal('100'),
            importo_pagato=Decimal('20'), applica_cassa=False, applica_iva=False,
        )
        self.client.force_login(self.a)
        url = reverse('storico_incassi', args=[parcella.pk])
        dati = {'chiave': uuid4(), 'data': date.today().isoformat(), 'importo': '30.00'}
        self.assertEqual(self.client.post(url, dati).status_code, 302)
        self.assertEqual(self.client.post(url, dati).status_code, 302)
        parcella.refresh_from_db()
        self.assertEqual(parcella.importo_pagato, Decimal('50'))
        self.assertEqual(parcella.stato, 'PARZIALE')
        self.assertEqual(self.client.get(url).context['saldo_storico'], Decimal('20'))
        dati.update(chiave=uuid4(), importo='51.00')
        self.assertContains(self.client.post(url, dati), 'supera il saldo residuo')
        dati.update(importo='50.00')
        self.assertEqual(self.client.post(url, dati).status_code, 302)
        parcella.refresh_from_db()
        self.assertEqual(parcella.stato, 'PAGATO')
        self.assertEqual(parcella.saldo_residuo, Decimal('0'))
        self.assertEqual(parcella.incassi.count(), 2)

    def test_generazione_parcella_da_ore(self):
        from decimal import Decimal
        from ore.models import VoceOra
        from parcelle.models import Parcella
        voce = VoceOra.objects.create(pratica=self.pa, utente=self.a, ore=2, tariffa_oraria=50)
        self.client.force_login(self.a)
        path = f'/ore/pratica/{self.pa.pk}/genera-parcella/'
        self.assertEqual(self.client.post(path).status_code, 302)
        parcella = Parcella.objects.get(pratica=self.pa)
        self.assertEqual(parcella.importo, Decimal('100'))
        voce.refresh_from_db()
        self.assertTrue(voce.inserita_in_parcella)
        self.assertEqual(voce.parcella_id, parcella.pk)
        self.client.post(path)
        self.assertEqual(Parcella.objects.filter(pratica=self.pa).count(), 1)
        parcella.delete()
        voce.refresh_from_db()
        self.assertFalse(voce.inserita_in_parcella)
        self.assertEqual(self.client.post(path).status_code, 302)
        voce.refresh_from_db()
        self.assertIsNotNone(voce.parcella_id)

    def test_archivi_altrui_non_accessibili(self):
        from django.urls import reverse
        from documenti.models import Documento
        from parcelle.models import Parcella
        from scadenze.models import Scadenza
        from ore.models import VoceOra
        doc = Documento.objects.create(pratica=self.pb, titolo='Altrui', file='qa-inesistente.pdf')
        parcella = Parcella.objects.create(pratica=self.pb, descrizione='Altrui', importo=10)
        scadenza = Scadenza.objects.create(pratica=self.pb, titolo='Altrui', data_scadenza=date.today())
        ore = VoceOra.objects.create(pratica=self.pb, ore=1)
        self.client.force_login(self.a)
        targets = [('dettaglio_pratica', self.pb.pk), ('modifica_immobile', self.ib.pk), ('elimina_documento', doc.pk), ('modifica_parcella', parcella.pk), ('modifica_scadenza', scadenza.pk), ('modifica_voce_ora', ore.pk)]
        for name, pk in targets:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name, args=[pk])).status_code, 404)

    def test_collaboratore_non_accede_consuntivo_ore(self):
        from ore.models import VoceOra
        user = User.objects.create_user('qa_collab_ore')
        ProfiloUtente.objects.create(user=user, studio=self.sa, ruolo='COLLABORATORE')
        voce = VoceOra.objects.create(pratica=self.pa, ore=1, tariffa_oraria=50)
        self.client.force_login(user)
        for path in [f'/ore/pratica/{self.pa.pk}/', f'/ore/pratica/{self.pa.pk}/nuova/', f'/ore/voce/{voce.pk}/modifica/', f'/ore/voce/{voce.pk}/elimina/']:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 403)
                self.assertEqual(self.client.post(path, {}).status_code, 403)

    def test_errore_fatturazione_annulla_tutta_operazione(self):
        from unittest.mock import patch
        from ore.models import VoceOra
        from parcelle.models import Parcella
        voce = VoceOra.objects.create(pratica=self.pa, utente=self.a, ore=2, tariffa_oraria=50)
        self.client.force_login(self.a)
        with patch('ore.views.Attivita.objects.create', side_effect=RuntimeError('Errore simulato')):
            with self.assertRaises(RuntimeError):
                self.client.post(f'/ore/pratica/{self.pa.pk}/genera-parcella/')
        self.assertFalse(Parcella.objects.filter(pratica=self.pa).exists())
        voce.refresh_from_db()
        self.assertFalse(voce.inserita_in_parcella)

    def test_webhook_non_firmato_non_attiva_pro(self):
        from django.test import override_settings
        with override_settings(STRIPE_WEBHOOK_SECRET='whsec_solo_prova'):
            response = self.client.post('/billing/webhook/', '{}', content_type='application/json')
            self.assertEqual(response.status_code, 400)
        self.sa.refresh_from_db()
        self.assertEqual(self.sa.piano, 'FREE')
