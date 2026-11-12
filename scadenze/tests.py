from datetime import timedelta
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.timezone import localdate
from agenda.models import EventoAgenda
from studi.models import Studio, ProfiloUtente
from clienti.models import Cliente
from immobili.models import Immobile
from pratiche.models import Pratica
from .models import Scadenza


@override_settings(LANCIO_BETA_FREE=True)
class PercorsoPrimaCILATests(TestCase):
    def test_registrazione_pratica_e_prima_scadenza(self):
        password = 'CILA-Collaudo-642!'
        registrazione = self.client.post('/accounts/registrazione/', {
            'nome_studio': 'Studio CILA', 'username': 'studio_cila_qa', 'email': 'cila@example.test',
            'password1': password, 'password2': password, 'accetta_privacy': 'on', 'accetta_termini': 'on',
        })
        self.assertRedirects(registrazione, reverse('home'))
        self.assertContains(self.client.get(reverse('home')), 'Crea la prima pratica')

        cliente = self.client.post(reverse('nuovo_cliente'), {'nome': 'Cliente CILA'}, HTTP_ACCEPT='application/json')
        self.assertEqual(cliente.status_code, 201)
        cliente_id = cliente.json()['id']
        immobile = self.client.post(reverse('nuovo_immobile'), {
            'cliente': cliente_id, 'comune': 'Treviso', 'indirizzo': 'Via di prova 1',
        }, HTTP_ACCEPT='application/json')
        self.assertEqual(immobile.status_code, 201)
        creazione = self.client.post(reverse('nuova_pratica'), {
            'cliente': cliente_id, 'immobile': immobile.json()['id'], 'comune': 'Treviso',
            'tipo_pratica': 'CILA', 'oggetto': 'CILA di collaudo', 'stato': 'IN_CORSO',
        })
        pratica = Pratica.objects.get(oggetto='CILA di collaudo')
        scheda = reverse('dettaglio_pratica', args=[pratica.pk])
        self.assertRedirects(creazione, scheda)
        self.assertTrue(pratica.workflow_pratica.fasi_pratica.exists())
        self.assertTrue(pratica.workflow_pratica.checklist_pratica.exists())
        self.assertNotContains(self.client.get(reverse('home')), 'Crea la prima pratica')

        nuova_scadenza = f'{reverse("nuova_scadenza")}?pratica={pratica.pk}'
        ritorno = f'{scheda}#scadenze-pratica'
        modulo = self.client.get(nuova_scadenza)
        self.assertEqual(modulo.context['form'].initial['pratica'], pratica.pk)
        self.assertContains(modulo, f'href="{ritorno}"')
        dati = {
            'pratica': pratica.pk, 'titolo': 'Sopralluogo CILA',
            'data_scadenza': (localdate() + timedelta(days=3)).isoformat(), 'priorita': 'ALTA',
        }
        errore = self.client.post(nuova_scadenza, {**dati, 'data_scadenza': ''})
        self.assertContains(errore, 'role="alert"')
        self.assertContains(errore, f'href="{ritorno}"')
        self.assertFalse(Scadenza.objects.filter(pratica=pratica, titolo=dati['titolo']).exists())

        self.assertRedirects(self.client.post(nuova_scadenza, dati), ritorno)
        dettaglio = self.client.get(scheda)
        self.assertContains(dettaglio, 'id="scadenze-pratica"')
        self.assertContains(dettaglio, dati['titolo'])
        self.assertContains(self.client.get(reverse('lista_scadenze')), dati['titolo'])
        self.assertTrue(EventoAgenda.objects.filter(pratica=pratica, titolo=f'Scadenza: {dati["titolo"]}').exists())

        self.assertRedirects(self.client.post(reverse('nuova_scadenza'), {**dati, 'titolo': 'Altra scadenza'}),
                             reverse('lista_scadenze'))


class ElencoScadenzeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('qa_scadenze')
        cls.studio = Studio.objects.create(nome='QA Alfa', titolare=cls.user)
        ProfiloUtente.objects.create(user=cls.user, studio=cls.studio, ruolo='TITOLARE')
        cliente = Cliente.objects.create(studio=cls.studio, nome='Cliente Ricercabile')
        immobile = Immobile.objects.create(studio=cls.studio, cliente=cliente, comune='QA')
        cls.pratica = Pratica.objects.create(studio=cls.studio, cliente=cliente, immobile=immobile, tipo_pratica='CILA', oggetto='Pratica Esempio', comune='QA')
        for n in range(33):
            Scadenza.objects.create(pratica=cls.pratica, titolo=f'QA Aperta {n:02d}', priorita='ALTA', data_scadenza=localdate() - timedelta(days=n == 0))
        Scadenza.objects.create(pratica=cls.pratica, titolo='QA Completata', completata=True, data_scadenza=localdate())
        cls.archivio = Scadenza.objects.create(pratica=cls.pratica, titolo='QA Archiviata', archiviata=True, priorita='BASSA', data_scadenza=localdate())
        cls.archivio_done = Scadenza.objects.create(pratica=cls.pratica, titolo='QA Archivio conclusa', archiviata=True, completata=True, data_scadenza=localdate())
        other = User.objects.create_user('qa_altro_studio')
        studio = Studio.objects.create(nome='QA Beta', titolare=other)
        cliente = Cliente.objects.create(studio=studio, nome='Cliente segreto')
        immobile = Immobile.objects.create(studio=studio, cliente=cliente, comune='QA')
        pratica = Pratica.objects.create(studio=studio, cliente=cliente, immobile=immobile, tipo_pratica='CILA', oggetto='Altrui', comune='QA')
        Scadenza.objects.create(pratica=pratica, titolo='SCADENZA ALTRO STUDIO', archiviata=True, data_scadenza=localdate())

    def setUp(self):
        self.client.force_login(self.user)

    def test_default_e_paginazione_stabile(self):
        response = self.client.get('/scadenze/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['scadenze']), 25)
        self.assertEqual(response.context['page_obj'].paginator.count, 33)
        first = {x.pk for x in response.context['scadenze']}
        response = self.client.get('/scadenze/?page=2')
        second = {x.pk for x in response.context['scadenze']}
        self.assertEqual(len(second), 8)
        self.assertFalse(first & second)

    def test_stati_e_conteggi_rispettano_studio(self):
        for state, total in [('aperte', 33), ('scadute', 1), ('completate', 1), ('archivio', 2)]:
            with self.subTest(state=state):
                response = self.client.get('/scadenze/', {'stato': state})
                self.assertEqual(response.context['page_obj'].paginator.count, total)
                self.assertNotContains(response, 'SCADENZA ALTRO STUDIO')
                self.assertEqual(response.context['conteggi'], {'aperte': 33, 'scadute': 1, 'completate': 1, 'archivio': 2})

    def test_archivio_solo_consultazione(self):
        response = self.client.get('/scadenze/?stato=archivio')
        self.assertContains(response, 'QA Archiviata')
        self.assertContains(response, 'QA Archivio conclusa')
        self.assertContains(response, 'Solo consultazione', count=2)
        for suffix in ['modifica/', 'elimina/', 'completa/']:
            self.assertNotContains(response, f'/scadenze/{self.archivio.pk}/{suffix}')
            self.assertEqual(self.client.post(f'/scadenze/{self.archivio.pk}/{suffix}', {'titolo': 'Modificata'}).status_code, 404)
        self.archivio.refresh_from_db()
        self.assertTrue(self.archivio.archiviata)
        self.assertEqual(self.archivio.titolo, 'QA Archiviata')

    def test_ricerca_per_titolo_pratica_cliente_e_priorita(self):
        for query in ['Aperta', 'Pratica Esempio', 'Cliente Ricercabile']:
            response = self.client.get('/scadenze/', {'q': query, 'priorita': 'ALTA'})
            self.assertEqual(response.context['page_obj'].paginator.count, 33)
            self.assertContains(response, 'priorita=ALTA')
        response = self.client.get('/scadenze/', {'stato': 'archivio', 'priorita': 'BASSA', 'q': 'Archiviata'})
        self.assertEqual(response.context['page_obj'].paginator.count, 1)

    def test_parametri_invalidi_ed_elenco_vuoto(self):
        response = self.client.get('/scadenze/', {'stato': 'ignoto', 'priorita': 'ignota', 'page': 'testo'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['stato'], 'aperte')
        self.assertEqual(response.context['priorita'], '')
        self.assertEqual(response.context['page_obj'].number, 1)
        response = self.client.get('/scadenze/', {'q': 'nessuna-corrispondenza'})
        self.assertContains(response, 'Nessuna scadenza corrisponde ai filtri.')

    def test_ricerca_non_espone_html(self):
        response = self.client.get('/scadenze/', {'q': '<script>esempio</script>'})
        self.assertNotContains(response, '<script>esempio</script>')
        self.assertContains(response, '&lt;script&gt;esempio&lt;/script&gt;')

    def test_admin_globale_vede_archivi_di_entrambi_studi(self):
        user = User.objects.create_superuser('qa_admin_scadenze', '', 'Solo-qa-832!')
        self.client.force_login(user)
        response = self.client.get('/scadenze/?stato=archivio')
        self.assertEqual(response.context['page_obj'].paginator.count, 3)
        self.assertContains(response, 'SCADENZA ALTRO STUDIO')

    def test_senza_profilo_non_legge_archivio(self):
        user = User.objects.create_user('qa_senza_profilo')
        self.client.force_login(user)
        self.assertEqual(self.client.get('/scadenze/?stato=archivio').status_code, 403)

    def test_dashboard_conta_solo_imminenti_e_nasconde_completate(self):
        self.studio.stato_abbonamento = 'ATTIVO'
        self.studio.save()
        Scadenza.objects.create(pratica=self.pratica, titolo='Oltre la settimana', data_scadenza=localdate()+timedelta(days=8))
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['scadenze_imminenti'], 32)
        self.assertContains(response, 'Scadenze nei prossimi 7 giorni')
        for scadenza in response.context['ultime_scadenze']:
            self.assertFalse(scadenza.completata)
            self.assertGreaterEqual(scadenza.data_scadenza, localdate())
