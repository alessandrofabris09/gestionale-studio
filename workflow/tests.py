from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase
from studi.models import Studio, ProfiloUtente
from clienti.models import Cliente
from immobili.models import Immobile
from pratiche.models import Pratica
from scadenze.models import Scadenza
from attivita.models import Attivita
from .models import TipoWorkflow, FaseWorkflow, ChecklistWorkflow, WorkflowPratica, FasePratica, ChecklistPratica


class AttivazioneSicuraTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('qa_workflow')
        studio = Studio.objects.create(nome='QA', titolare=self.owner)
        ProfiloUtente.objects.create(user=self.owner, studio=studio, ruolo='TITOLARE')
        cliente = Cliente.objects.create(studio=studio, nome='QA')
        immobile = Immobile.objects.create(studio=studio, cliente=cliente, comune='QA')
        self.pratica = Pratica.objects.create(studio=studio, cliente=cliente, immobile=immobile, tipo_pratica='CILA', oggetto='QA', comune='QA')
        self.workflow = TipoWorkflow.objects.create(nome='QA', categoria='EDILIZIA')
        FaseWorkflow.objects.create(workflow=self.workflow, titolo='Fase QA', giorni_scadenza=10)
        ChecklistWorkflow.objects.create(workflow=self.workflow, voce='Voce QA')
        self.path = f'/workflow/pratica/{self.pratica.pk}/attiva/'
        self.client.force_login(self.owner)

    def test_apertura_modulo_e_post_invalido_non_creano_record(self):
        self.assertEqual(self.client.get(self.path).status_code, 200)
        self.assertFalse(WorkflowPratica.objects.exists())
        self.assertEqual(self.client.post(self.path, {'workflow': '99999'}).status_code, 200)
        self.assertFalse(WorkflowPratica.objects.exists())

    def test_attivazione_e_ripetizione_preservano_stato(self):
        data = {'workflow': self.workflow.pk, 'note': 'Prima nota'}
        self.assertEqual(self.client.post(self.path, data).status_code, 302)
        fase = FasePratica.objects.get()
        fase.completata = True
        fase.save()
        voce = ChecklistPratica.objects.get()
        voce.completato = True
        voce.save()
        data['note'] = 'Nota aggiornata'
        self.assertEqual(self.client.post(self.path, data).status_code, 302)
        self.assertEqual(FasePratica.objects.count(), 1)
        fase.refresh_from_db()
        voce.refresh_from_db()
        self.assertTrue(fase.completata)
        self.assertTrue(voce.completato)
        self.assertEqual(Scadenza.objects.count(), 1)
        self.assertEqual(Attivita.objects.count(), 1)
        self.assertEqual(WorkflowPratica.objects.get().note, 'Nota aggiornata')

    def test_errore_ripristina_workflow_precedente(self):
        self.client.post(self.path, {'workflow': self.workflow.pk})
        old = WorkflowPratica.objects.get()
        old_fase = FasePratica.objects.get().pk
        other = TipoWorkflow.objects.create(nome='QA secondo', categoria='EDILIZIA')
        FaseWorkflow.objects.create(workflow=other, titolo='Seconda fase', giorni_scadenza=3)
        with patch('workflow.views.FasePratica.objects.create', side_effect=RuntimeError('Errore simulato')):
            with self.assertRaises(RuntimeError):
                self.client.post(self.path, {'workflow': other.pk})
        old.refresh_from_db()
        self.assertEqual(old.workflow_id, self.workflow.pk)
        self.assertTrue(FasePratica.objects.filter(pk=old_fase).exists())
        self.assertEqual(Scadenza.objects.count(), 1)

    def test_cambio_archivia_solo_scadenze_generate(self):
        from datetime import date
        self.client.post(self.path, {'workflow': self.workflow.pk})
        auto = Scadenza.objects.get()
        self.assertEqual(auto.workflow_origine_id, WorkflowPratica.objects.get().pk)
        manuale = Scadenza.objects.create(pratica=self.pratica, titolo='Manuale', data_scadenza=date.today())
        legacy = Scadenza.objects.create(pratica=self.pratica, titolo='Fase QA', descrizione='Fase workflow: Fase QA', data_scadenza=auto.data_scadenza)
        other = TipoWorkflow.objects.create(nome='Nuovo QA', categoria='EDILIZIA')
        FaseWorkflow.objects.create(workflow=other, titolo='Nuova fase', giorni_scadenza=5)
        self.assertEqual(self.client.post(self.path, {'workflow': other.pk}).status_code, 302)
        auto.refresh_from_db()
        manuale.refresh_from_db()
        legacy.refresh_from_db()
        self.assertTrue(auto.archiviata)
        self.assertFalse(manuale.archiviata)
        self.assertFalse(legacy.archiviata)
        self.assertEqual(Scadenza.objects.count(), 4)
        response = self.client.get('/scadenze/')
        self.assertContains(response, 'Manuale')
        self.assertContains(response, 'Nuova fase')
        self.assertNotContains(response, f'/scadenze/{auto.pk}/modifica/')
        self.assertEqual(self.client.get(f'/scadenze/{auto.pk}/modifica/').status_code, 404)

    def test_errore_cambio_ripristina_anche_archiviazione(self):
        self.client.post(self.path, {'workflow': self.workflow.pk})
        auto = Scadenza.objects.get()
        other = TipoWorkflow.objects.create(nome='Altro QA', categoria='EDILIZIA')
        FaseWorkflow.objects.create(workflow=other, titolo='Altra fase', giorni_scadenza=3)
        with patch('workflow.views.FasePratica.objects.create', side_effect=RuntimeError('Errore simulato')):
            with self.assertRaises(RuntimeError):
                self.client.post(self.path, {'workflow': other.pk})
        auto.refresh_from_db()
        self.assertFalse(auto.archiviata)
        self.assertEqual(Scadenza.objects.count(), 1)

    def test_workflow_automatico_registra_origine(self):
        from pratiche.views import attiva_workflow_automatico
        self.pratica.tipo_pratica = self.workflow.nome
        self.pratica.save()
        instance = attiva_workflow_automatico(self.pratica)
        self.assertEqual(Scadenza.objects.get().workflow_origine_id, instance.pk)

    def test_form_manuale_non_modifica_origine_o_archivio(self):
        from scadenze.forms import ScadenzaForm
        form = ScadenzaForm()
        self.assertNotIn('workflow_origine', form.fields)
        self.assertNotIn('archiviata', form.fields)

    def test_archiviata_non_compare_in_calendario(self):
        self.client.post(self.path, {'workflow': self.workflow.pk})
        auto = Scadenza.objects.get()
        auto.archiviata = True
        auto.save()
        response = self.client.get('/scadenze/eventi/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Fase QA', response.content.decode())


    def test_archiviata_esclusa_da_email_dashboard_e_ics(self):
        from datetime import date
        from scadenze.views import invia_email_scadenze_leggera
        self.client.post(self.path, {'workflow': self.workflow.pk})
        auto = Scadenza.objects.get()
        auto.archiviata = True
        auto.data_scadenza = date.today()
        auto.save()
        studio = self.pratica.studio
        studio.stato_abbonamento = 'ATTIVO'
        studio.calendario_ics_token = 'a' * 64
        studio.save()
        self.assertEqual(invia_email_scadenze_leggera(studio), 'Nessuna scadenza da notificare.')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['tot_scadenze'], 0)
        response = self.client.get('/agenda/calendario/' + 'a' * 64 + '/.ics')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Fase QA', response.content.decode())
