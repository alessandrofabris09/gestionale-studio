from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from studi.models import Studio

from .models import IscrizioneFreeLancio


@override_settings(LANCIO_BETA_FREE=True, BETA_PRO_CANDIDATURA_URL='https://demo.example.test/pro/')
class LancioFreeTests(TestCase):
    def test_registrazione_free_reale_contata_e_senza_scadenza(self):
        precedente = User.objects.create_user('studio_precedente')
        Studio.objects.create(nome='Studio preesistente', titolare=precedente)
        visitatore = Client()
        home = visitatore.get('/')
        self.assertContains(home, '0 / 100 studi Free registrati')
        self.assertContains(home, '<video controls', html=False)
        self.assertNotContains(home, 'https://demo.example.test/pro/')
        self.assertRedirects(visitatore.get('/utenti/registrazione/'), '/accounts/registrazione/')

        signup = visitatore.post('/accounts/registrazione/', {
            'nome_studio': 'Studio campagna', 'username': 'studio_campagna', 'email': 'campagna@example.test',
            'password1': 'CollaudoLancio!449', 'password2': 'CollaudoLancio!449',
            'accetta_privacy': 'on', 'accetta_termini': 'on',
        })
        self.assertEqual(signup.status_code, 302)
        studio = Studio.objects.get(titolare__username='studio_campagna')
        self.assertEqual((studio.piano, studio.stato_abbonamento, studio.trial_fino_al), ('FREE', 'ATTIVO', None))
        self.assertEqual(studio.limite_pratiche, 20)
        self.assertEqual(IscrizioneFreeLancio.attive().get().studio, studio)
        self.assertContains(visitatore.get('/lancio/'), '1 / 100 studi Free registrati')
        with patch('django.utils.timezone.now', return_value=timezone.now() + timedelta(days=40)):
            visitatore.force_login(studio.titolare)
            self.assertContains(visitatore.get('/dashboard/'), 'Segui il lancio della beta PRO')
        self.assertNotContains(visitatore.get('/studi/abbonamento/'), '/billing/checkout/pro/')

    def test_soglia_e_ordine_delle_iscrizioni_attive(self):
        utente = User.objects.create_user('ordine_lancio')
        studi = Studio.objects.bulk_create([
            Studio(nome=f'Studio {indice}', titolare=utente) for indice in range(101)
        ])
        IscrizioneFreeLancio.objects.bulk_create([IscrizioneFreeLancio(studio=studio) for studio in studi])
        studi[0].attivo = False
        studi[0].save(update_fields=['attivo'])
        response = self.client.get('/lancio/')
        self.assertContains(response, '100 / 100 studi Free registrati')
        self.assertContains(response, 'Obiettivo raggiunto')
        self.assertEqual(list(IscrizioneFreeLancio.attive().values_list('studio_id', flat=True)[:15]),
                         [studio.pk for studio in studi[1:16]])
