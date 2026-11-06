"""Verifiche indipendenti, solo dati fittizi e storage temporaneo."""
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from types import SimpleNamespace

from stripe import Event

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings, Client
from django.urls import reverse
from django.utils.timezone import localdate

from studi.models import Studio, ProfiloUtente
from clienti.models import Cliente
from immobili.models import Immobile
from pratiche.models import Pratica
from documenti.models import Documento
from parcelle.models import Parcella
from agenda.models import EventoAgenda
from scadenze.models import Scadenza
from ore.models import VoceOra
from workflow.models import TipoWorkflow, FaseWorkflow, WorkflowPratica


class BaseQA(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.users={}
        for role in ['TITOLARE','TECNICO','SEGRETERIA','COLLABORATORE']:
            cls.users[role]=User.objects.create_user('qa_'+role.lower())
        cls.admin=User.objects.create_superuser('qa_globale','','Password-test!741')
        cls.studio=Studio.objects.create(nome='QA Alfa',titolare=cls.users['TITOLARE'],stato_abbonamento='ATTIVO',limite_utenti=10)
        for role,user in cls.users.items():
            ProfiloUtente.objects.create(user=user,studio=cls.studio,ruolo=role)
        other=User.objects.create_user('qa_beta')
        cls.other=Studio.objects.create(nome='QA Beta',titolare=other,stato_abbonamento='ATTIVO')
        ProfiloUtente.objects.create(user=other,studio=cls.other,ruolo='TITOLARE')
        cls.clients=[]; cls.properties=[]; cls.practices=[]; cls.invoices=[]; cls.events=[]; cls.deadlines=[]; cls.docs=[]
        for n,studio in enumerate([cls.studio,cls.other]):
            cliente=Cliente.objects.create(studio=studio,nome=f'CLIENTE-QA-{n}',email=f'cliente{n}@example.test')
            immobile=Immobile.objects.create(studio=studio,cliente=cliente,comune=f'Comune QA {n}')
            pratica=Pratica.objects.create(studio=studio,cliente=cliente,immobile=immobile,tipo_pratica='Procedura QA',oggetto=f'PRATICA-QA-{n}',comune='QA')
            parcella=Parcella.objects.create(pratica=pratica,descrizione=f'PARCELLA-RISERVATA-QA-{n}',importo=Decimal('100'),applica_cassa=True,aliquota_cassa=Decimal('5'),applica_iva=True,iva=Decimal('22'))
            evento=EventoAgenda.objects.create(studio=studio,titolo=f'EVENTO-QA-{n}',data=localdate(),cliente=cliente,pratica=pratica)
            scadenza=Scadenza.objects.create(pratica=pratica,titolo=f'SCADENZA-QA-{n}',data_scadenza=localdate())
            documento=Documento.objects.create(pratica=pratica,titolo=f'DOCUMENTO-QA-{n}',file=f'inesistente-qa-{n}.pdf')
            for target,value in [(cls.clients,cliente),(cls.properties,immobile),(cls.practices,pratica),(cls.invoices,parcella),(cls.events,evento),(cls.deadlines,scadenza),(cls.docs,documento)]:
                target.append(value)
        cls.workflow=TipoWorkflow.objects.create(nome='Procedura QA',categoria='EDILIZIA')

    def setUp(self):
        self.temp=TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.override=override_settings(BASE_DIR=Path(self.temp.name),MEDIA_ROOT=Path(self.temp.name)/'media')
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.client.force_login(self.users['TITOLARE'])


class RuoliQA(BaseQA):
    pass

ROUTES={
    '/clienti/': {'TITOLARE','TECNICO','SEGRETERIA'},
    '/immobili/': {'TITOLARE','TECNICO','SEGRETERIA'},
    '/pratiche/': {'TITOLARE','TECNICO','SEGRETERIA'},
    '/documenti/': {'TITOLARE','TECNICO','SEGRETERIA'},
    '/parcelle/': {'TITOLARE','SEGRETERIA'},
    '/agenda/': {'TITOLARE','TECNICO','SEGRETERIA','COLLABORATORE'},
    '/scadenze/': {'TITOLARE','TECNICO','SEGRETERIA','COLLABORATORE'},
    '/utenti/': {'TITOLARE'},
    '/studi/utenti/': {'TITOLARE'},
    '/studi/abbonamento/': {'TITOLARE'},
    '/scadenze/alert/': {'TITOLARE','TECNICO'},
}
def permission_case(role,path,allowed):
    def test(self):
        self.client.force_login(self.users[role])
        response=self.client.get(path)
        if role not in allowed and path=='/studi/abbonamento/':
            self.assertEqual(response.status_code,302)
            self.assertIn(response['Location'],['/dashboard/','/login/'])
        else:
            self.assertEqual(response.status_code,200 if role in allowed else 403)
    return test
for path,allowed in ROUTES.items():
    for role in ['TITOLARE','TECNICO','SEGRETERIA','COLLABORATORE']:
        setattr(RuoliQA,'test_'+role.lower()+'_'+path.strip('/').replace('/','_'),permission_case(role,path,allowed))


class ElencoPraticheQA(BaseQA):
    def test_scadenze_dalla_scheda_pratica(self):
        pratica = self.practices[0]
        self.deadlines[0].archiviata = True
        self.deadlines[0].save(update_fields=['archiviata'])
        url = reverse('nuova_scadenza')
        form = self.client.get(url, {'pratica': pratica.pk})
        self.assertEqual(form.context['form']['pratica'].value(), pratica.pk)
        estranea = self.client.get(url, {'pratica': self.practices[1].pk})
        self.assertIsNone(estranea.context['form']['pratica'].value())
        creazione = self.client.post(url, {
            'pratica': pratica.pk, 'titolo': 'Scadenza dalla scheda',
            'data_scadenza': localdate().isoformat(), 'priorita': 'MEDIA',
        })
        self.assertRedirects(creazione, reverse('lista_scadenze'))
        scheda = self.client.get(reverse('dettaglio_pratica', args=[pratica.pk]))
        self.assertContains(scheda, 'Scadenza dalla scheda')
        self.assertNotContains(scheda, self.deadlines[0].titolo)
        self.assertNotContains(scheda, self.deadlines[1].titolo)

    def test_filtri_e_paginazione_rispettano_lo_studio(self):
        Pratica.objects.filter(pk=self.practices[1].pk).update(tipo_pratica='Tipo riservato')
        Pratica.objects.bulk_create([
            Pratica(
                studio=self.studio, cliente=self.clients[0], immobile=self.properties[0],
                tipo_pratica='Procedura QA', oggetto='Pratica da ritrovare',
                comune='QA', stato='IN_CORSO',
            )
            for _ in range(26)
        ])
        url = reverse('lista_pratiche')
        filtri = {'ricerca': 'ritrovare', 'stato': 'IN_CORSO', 'tipo': 'Procedura QA'}
        prima = self.client.get(url, filtri)
        self.assertEqual(len(prima.context['pagina'].object_list), 25)
        self.assertEqual(prima.context['pagina'].paginator.count, 26)
        self.assertContains(prima, 'stato=IN_CORSO&amp;tipo=Procedura+QA&amp;page=2')
        self.assertNotContains(prima, 'Tipo riservato')
        seconda = self.client.get(url, {**filtri, 'page': 2, 'stato': 'IN CORSO'})
        self.assertEqual(len(seconda.context['pagina'].object_list), 1)
        self.assertEqual(seconda.context['stato'], 'IN_CORSO')


class IsolamentoQA(BaseQA):
    def test_get_e_post_archivi_altrui(self):
        targets=[('dettaglio_cliente',self.clients[1].pk),('modifica_cliente',self.clients[1].pk),('elimina_cliente',self.clients[1].pk),('dettaglio_immobile',self.properties[1].pk),('modifica_immobile',self.properties[1].pk),('elimina_immobile',self.properties[1].pk),('dettaglio_pratica',self.practices[1].pk),('modifica_pratica',self.practices[1].pk),('elimina_pratica',self.practices[1].pk),('pdf_pratica',self.practices[1].pk),('modifica_parcella',self.invoices[1].pk),('elimina_parcella',self.invoices[1].pk),('pdf_parcella',self.invoices[1].pk),('modifica_evento',self.events[1].pk),('elimina_evento',self.events[1].pk),('modifica_scadenza',self.deadlines[1].pk),('elimina_scadenza',self.deadlines[1].pk),('carica_documento',self.practices[1].pk),('carica_documenti_multipli',self.practices[1].pk),('elimina_documento',self.docs[1].pk)]
        for name,pk in targets:
            for method in [self.client.get,self.client.post]:
                with self.subTest(route=name,method=method.__name__):
                    self.assertEqual(method(reverse(name,args=[pk]),{}).status_code,404)

    def test_campi_collegati_non_accettano_altri_studi(self):
        from immobili.forms import ImmobileForm
        from pratiche.forms import PraticaForm
        from agenda.forms import EventoAgendaForm
        from parcelle.forms import ParcellaForm
        from scadenze.forms import ScadenzaForm
        cases=[(ImmobileForm,'cliente',self.clients[1].pk),(PraticaForm,'cliente',self.clients[1].pk),(PraticaForm,'immobile',self.properties[1].pk),(EventoAgendaForm,'cliente',self.clients[1].pk),(EventoAgendaForm,'pratica',self.practices[1].pk),(ParcellaForm,'pratica',self.practices[1].pk),(ScadenzaForm,'pratica',self.practices[1].pk)]
        for cls,field,foreign in cases:
            with self.subTest(form=cls.__name__,field=field):
                form=cls(studio=self.studio)
                self.assertFalse(form.fields[field].queryset.filter(pk=foreign).exists())

    def test_tecnico_non_legge_parcelle_dal_dettaglio_pratica(self):
        self.client.force_login(self.users['TECNICO'])
        self.assertEqual(self.client.get('/parcelle/').status_code,403)
        response=self.client.get(reverse('dettaglio_pratica',args=[self.practices[0].pk]))
        self.assertNotIn(self.invoices[0].descrizione,response.content.decode())

    def test_token_calendario_errato_e_separazione_studi(self):
        self.studio.calendario_ics_token='a'*64; self.studio.save()
        self.other.calendario_ics_token='b'*64; self.other.save()
        self.assertEqual(self.client.get(reverse('calendario_ics',args=['errato'])).status_code,403)
        response=self.client.get(reverse('calendario_ics',args=['a'*64]))
        self.assertContains(response,'EVENTO-QA-0')
        self.assertNotContains(response,'EVENTO-QA-1')


class OperazioniQA(BaseQA):
    def test_parcella_numero_manuale_duplicato_rifiutato(self):
        from parcelle.forms import ParcellaForm
        data={'pratica':self.practices[0].pk,'tipo_documento':'PARCELLA','numero_documento':self.invoices[0].numero_documento,'descrizione':'Duplicata QA','importo':'100','stato':'DA_PAGARE','tipo_cassa':'NESSUNA'}
        form=ParcellaForm(data,studio=self.studio)
        self.assertFalse(form.is_valid())
        self.assertIn('numero_documento',form.errors)

    def test_ore_tariffa_negativa_rifiutata_e_zero_consentito(self):
        from ore.forms import VoceOraForm
        data={'data':str(localdate()),'tipo_attivita':'ALTRO','ore':'2','tariffa_oraria':'-50'}
        self.assertFalse(VoceOraForm(data).is_valid())
        data['tariffa_oraria']='0'
        self.assertTrue(VoceOraForm(data).is_valid())

    def test_upload_multiplo(self):
        from documenti.forms import DocumentoMultiploForm
        data={'tipo_documento':'ALTRO','files':[SimpleUploadedFile('multi-uno.pdf',b'%PDF-1.4\nQA'),SimpleUploadedFile('multi-due.pdf',b'%PDF-1.4\nQA')]}
        response=self.client.post(reverse('carica_documenti_multipli',args=[self.practices[0].pk]),data)
        self.assertEqual(response.status_code,302)
        self.assertEqual(Documento.objects.filter(pratica=self.practices[0]).count(),3)

    def test_csrf_su_operazioni_principali(self):
        client=Client(enforce_csrf_checks=True)
        client.force_login(self.users['TITOLARE'])
        paths=['/clienti/nuovo/','/immobili/nuovo/','/pratiche/nuova/','/parcelle/nuova/','/agenda/nuovo/','/scadenze/nuova/',reverse('carica_documento',args=[self.practices[0].pk]),reverse('nuova_voce_ora',args=[self.practices[0].pk])]
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(client.post(path,{}).status_code,403)

    def test_pdf_non_espone_dati_altro_studio(self):
        from reportlab.pdfgen.canvas import Canvas
        def uncompressed(*args,**kwargs):
            kwargs['pageCompression']=0
            return Canvas(*args,**kwargs)
        with patch('pratiche.views.canvas.Canvas',side_effect=uncompressed):
            for name,pk in [('pdf_pratica',self.practices[0].pk),('pdf_parcella',self.invoices[0].pk)]:
                response=self.client.get(reverse(name,args=[pk]))
                content=b''.join(response.streaming_content) if response.streaming else response.content
                self.assertIn(b'CLIENTE-QA-0',content)
                self.assertNotIn(b'CLIENTE-QA-1',content)

    def test_cliente_creazione_modifica_eliminazione(self):
        response=self.client.post('/clienti/nuovo/',{'nome':'Cliente Nuovo QA'})
        self.assertEqual(response.status_code,302)
        obj=Cliente.objects.get(nome='Cliente Nuovo QA')
        self.assertEqual(obj.studio_id,self.studio.pk)
        self.assertEqual(self.client.post(reverse('modifica_cliente',args=[obj.pk]),{'nome':'Cliente Aggiornato QA'}).status_code,302)
        self.assertEqual(self.client.post(reverse('elimina_cliente',args=[obj.pk])).status_code,302)
        self.assertFalse(Cliente.objects.filter(pk=obj.pk).exists())

    def test_immobile_creazione_modifica_eliminazione(self):
        data={'cliente':self.clients[0].pk,'comune':'Nuovo Comune QA'}
        self.assertEqual(self.client.post('/immobili/nuovo/',data).status_code,302)
        obj=Immobile.objects.get(comune='Nuovo Comune QA')
        data['comune']='Comune Modificato QA'
        self.assertEqual(self.client.post(reverse('modifica_immobile',args=[obj.pk]),data).status_code,302)
        self.assertEqual(self.client.post(reverse('elimina_immobile',args=[obj.pk])).status_code,302)

    def test_pratica_creazione_con_workflow(self):
        data={'cliente':self.clients[0].pk,'immobile':self.properties[0].pk,'tipo_pratica':self.workflow.nome,'oggetto':'NUOVA PRATICA QA','comune':'QA','stato':'IN_CORSO'}
        self.assertEqual(self.client.post('/pratiche/nuova/',data).status_code,302)
        obj=Pratica.objects.get(oggetto='NUOVA PRATICA QA')
        self.assertTrue(WorkflowPratica.objects.filter(pratica=obj).exists())
        data['oggetto']='PRATICA AGGIORNATA QA'
        self.assertEqual(self.client.post(reverse('modifica_pratica',args=[obj.pk]),data).status_code,302)
        self.assertEqual(self.client.post(reverse('elimina_pratica',args=[obj.pk])).status_code,302)

    def test_evento_creazione_completamento_eliminazione(self):
        data={'titolo':'NUOVO EVENTO QA','tipo':'ALTRO','priorita':'MEDIA','data':str(localdate()),'cliente':self.clients[0].pk,'pratica':self.practices[0].pk}
        self.assertEqual(self.client.post('/agenda/nuovo/',data).status_code,302)
        obj=EventoAgenda.objects.get(titolo=data['titolo'])
        self.assertEqual(self.client.post(reverse('completa_evento',args=[obj.pk])).status_code,302)
        obj.refresh_from_db(); self.assertTrue(obj.completato)
        self.assertEqual(self.client.post(reverse('elimina_evento',args=[obj.pk])).status_code,302)

    def test_scadenza_creazione_completamento_eliminazione(self):
        data={'titolo':'NUOVA SCADENZA QA','priorita':'MEDIA','data_scadenza':str(localdate()),'pratica':self.practices[0].pk}
        self.assertEqual(self.client.post('/scadenze/nuova/',data).status_code,302)
        obj=Scadenza.objects.get(titolo=data['titolo'])
        self.assertEqual(self.client.post(reverse('completa_scadenza',args=[obj.pk])).status_code,302)
        obj.refresh_from_db(); self.assertTrue(obj.completata)
        self.assertEqual(self.client.post(reverse('elimina_scadenza',args=[obj.pk])).status_code,302)

    def test_documento_upload_e_eliminazione_locale(self):
        data={'titolo':'UPLOAD QA','tipo_documento':'ALTRO','file':SimpleUploadedFile('qa.pdf',b'%PDF-1.4\nDati fittizi',content_type='application/pdf')}
        response=self.client.post(reverse('carica_documento',args=[self.practices[0].pk]),data)
        self.assertEqual(response.status_code,302)
        obj=Documento.objects.get(titolo='UPLOAD QA'); name=obj.file.path
        self.assertTrue(Path(name).is_file())
        self.assertEqual(self.client.post(reverse('elimina_documento',args=[obj.pk])).status_code,302)
        self.assertFalse(Path(name).exists())

    def test_pdf_pratica_e_parcella(self):
        for name,pk in [('pdf_pratica',self.practices[0].pk),('pdf_parcella',self.invoices[0].pk)]:
            with self.subTest(pdf=name):
                response=self.client.get(reverse(name,args=[pk]))
                self.assertEqual(response.status_code,200)
                content=b''.join(response.streaming_content) if response.streaming else response.content
                self.assertTrue(content.startswith(b'%PDF'))

    def test_numeri_parcella_non_duplicati_dopo_cancellazione(self):
        first=self.invoices[0]
        second=Parcella.objects.create(pratica=self.practices[0],descrizione='Seconda',importo=20)
        first.delete()
        third=Parcella.objects.create(pratica=self.practices[0],descrizione='Terza',importo=30)
        self.assertNotEqual(second.numero_documento,third.numero_documento)

    def test_calcoli_parcella_e_stati_pagamento(self):
        obj=self.invoices[0]
        self.assertEqual(obj.importo_cassa,Decimal('5'))
        self.assertEqual(obj.importo_iva,Decimal('23.1'))
        self.assertEqual(obj.totale_documento,Decimal('128.1'))
        obj.importo_pagato=Decimal('50'); obj.save(); self.assertEqual(obj.stato,'PARZIALE')
        obj.importo_pagato=obj.totale_documento; obj.save(); self.assertEqual(obj.stato,'PAGATO')

    def test_ore_negative_rifiutate(self):
        from ore.forms import VoceOraForm
        form=VoceOraForm({'data':str(localdate()),'tipo_attivita':'ALTRO','ore':'-2','tariffa_oraria':'50'})
        self.assertFalse(form.is_valid())

    def test_workflow_automatico_errore_non_lascia_pratica_parziale(self):
        FaseWorkflow.objects.create(workflow=self.workflow,titolo='Fase QA')
        data={'cliente':self.clients[0].pk,'immobile':self.properties[0].pk,'tipo_pratica':self.workflow.nome,'oggetto':'PRATICA DA ANNULLARE QA','comune':'QA','stato':'IN_CORSO'}
        with patch('pratiche.views.FasePratica.objects.create',side_effect=RuntimeError('Errore simulato')):
            with self.assertRaises(RuntimeError):
                self.client.post('/pratiche/nuova/',data)
        self.assertFalse(Pratica.objects.filter(oggetto='PRATICA DA ANNULLARE QA').exists())

    def test_ruolo_proprio_non_modificabile(self):
        profile=ProfiloUtente.objects.get(user=self.users['TITOLARE'])
        self.client.post(reverse('modifica_ruolo_utente',args=[profile.pk]),{'ruolo':'TECNICO','email':'qa@example.test'})
        profile.refresh_from_db(); self.assertEqual(profile.ruolo,'TITOLARE')


class WebhookQA(BaseQA):
    def send(self,event):
        stripe_event = Event.construct_from(event, None)
        with patch('billing.views.stripe.Webhook.construct_event', return_value=stripe_event):
            response=self.client.post('/billing/webhook/','{}',content_type='application/json')
            self.assertEqual(response.status_code,200)

    def test_annullamento_e_pagamento_fallito(self):
        for event_type in ['invoice.payment_failed','customer.subscription.deleted']:
            self.studio.piano='PRO'; self.studio.stato_abbonamento='ATTIVO'; self.studio.stripe_subscription_id='sub_qa'; self.studio.save()
            obj={'id':'sub_qa','subscription':'sub_qa'}
            self.send({'type':event_type,'data':{'object':obj}})
            self.studio.refresh_from_db(); self.assertFalse(self.studio.is_pro())

    def test_evento_sconosciuto_non_modifica_studio(self):
        self.send({'type':'qa.evento.sconosciuto','data':{'object':{}}})
        self.studio.refresh_from_db(); self.assertEqual(self.studio.piano,'FREE')
