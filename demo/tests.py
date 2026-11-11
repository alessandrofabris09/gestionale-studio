from datetime import timedelta
from io import StringIO
from unittest import SkipTest
from unittest.mock import patch

from django.apps import apps
from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

if not apps.is_installed('demo'):
    raise SkipTest('La demo si verifica con gestionale.settings_demo.')

from .models import VERSIONE_CONSENSO, RichiestaPro


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class DemoTests(TestCase):
    def setUp(self):
        cache.clear()
        self.lista = reverse('demo_lista')
        self.form = {'email': 'Studio@Example.com', 'consenso': 'on'}

    def test_demo_pubblica_separata_e_senza_cookie(self):
        for nome in ('demo_home', 'demo_prova', 'demo_privacy', 'demo_cookie', 'demo_termini'):
            with self.subTest(nome=nome):
                response = self.client.get(reverse(nome))
                self.assertEqual(response.status_code, 200)
                self.assertFalse(response.cookies)
                self.assertIn("default-src 'self'", response['Content-Security-Policy'])
        for url in ('/dashboard/', '/billing/checkout/', '/admin/', '/accounts/registrazione/'):
            self.assertEqual(self.client.get(url).status_code, 404)

    def test_consenso_esplicito_e_cookie_csrf(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(self.lista, self.form).status_code, 403)
        response = client.get(self.lista)
        self.assertEqual(response['Referrer-Policy'], 'same-origin')
        cookie = response.cookies['csrftoken']
        self.assertEqual(cookie['max-age'], 86400)
        self.assertTrue(cookie['httponly'])
        response = client.post(self.lista, {'email': self.form['email'], 'csrfmiddlewaretoken': cookie.value})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(RichiestaPro.objects.exists())
        self.assertFalse(mail.outbox)

    def test_condizioni_visibili_prima_della_candidatura(self):
        self.assertContains(self.client.get(reverse('demo_home')), 'Candidati alla beta PRO')
        for url in (self.lista, reverse('demo_termini')):
            response = self.client.get(url)
            for testo in ('15 studi', '6 mesi', '500 MB', '30 giorni prima', 'sola lettura', 'rinnovo automatico'):
                self.assertContains(response, testo)
        self.assertContains(self.client.get(reverse('demo_privacy')), VERSIONE_CONSENSO)

    def test_richiesta_conferma_e_revoca(self):
        self.assertEqual(self.client.post(self.lista, self.form).status_code, 302)
        richiesta = RichiestaPro.objects.get()
        self.assertEqual(richiesta.email, 'studio@example.com')
        self.assertEqual(richiesta.versione_consenso, VERSIONE_CONSENSO)
        conferma = reverse('demo_conferma', args=[richiesta.token])
        revoca = reverse('demo_ritira', args=[richiesta.token_revoca])
        self.assertIn(conferma, mail.outbox[0].body)
        self.assertIn(revoca, mail.outbox[0].body)
        self.client.get(conferma)
        self.assertContains(self.client.get(self.lista), '0 candidature confermate')
        self.client.post(conferma)
        self.client.post(conferma)
        self.assertContains(self.client.get(self.lista), '1 candidatura confermata')
        self.client.post(self.lista, {'email': 'studio@example.com', 'consenso': 'on'})
        self.assertEqual(len(mail.outbox), 1)
        self.client.get(revoca)
        self.assertTrue(RichiestaPro.objects.exists())
        self.client.post(revoca)
        self.assertFalse(RichiestaPro.objects.exists())
        self.assertContains(self.client.get(self.lista), '0 candidature confermate')

    def test_il_consenso_precedente_non_conta_come_candidatura(self):
        richiesta = RichiestaPro.objects.create(
            email='studio@example.com', versione_consenso='demo-pro-v1', confermata_il=timezone.now(),
        )
        vecchio_link = reverse('demo_conferma', args=[richiesta.token])
        self.assertContains(self.client.get(self.lista), '0 candidature confermate')
        self.assertEqual(self.client.post(vecchio_link).status_code, 410)
        self.assertEqual(self.client.post(self.lista, self.form).status_code, 302)
        richiesta.refresh_from_db()
        self.assertEqual(richiesta.versione_consenso, VERSIONE_CONSENSO)
        self.assertIsNone(richiesta.confermata_il)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(self.client.post(reverse('demo_conferma', args=[richiesta.token])).status_code, 200)
        self.assertContains(self.client.get(self.lista), '1 candidatura confermata')

    def test_link_scaduto_e_nuova_richiesta(self):
        self.client.post(self.lista, self.form)
        richiesta = RichiestaPro.objects.get()
        vecchio_token = richiesta.token
        RichiestaPro.objects.update(richiesta_il=timezone.now() - timedelta(hours=25))
        self.assertEqual(self.client.post(reverse('demo_conferma', args=[vecchio_token])).status_code, 410)
        self.client.post(self.lista, self.form)
        richiesta.refresh_from_db()
        self.assertNotEqual(richiesta.token, vecchio_token)
        self.assertEqual(len(mail.outbox), 2)

    def test_pulizia_e_contatore(self):
        now = timezone.now()
        RichiestaPro.objects.create(email='scaduta@example.com', richiesta_il=now - timedelta(days=2))
        RichiestaPro.objects.create(email='vecchia@example.com', confermata_il=now - timedelta(days=366))
        RichiestaPro.objects.create(
            email='attiva@example.com', confermata_il=now, versione_consenso=VERSIONE_CONSENSO,
        )
        self.assertContains(self.client.get(reverse('demo_home')), '1 candidatura confermata')
        call_command('pulisci_lista_pro', stdout=StringIO())
        self.assertEqual(RichiestaPro.objects.get().email, 'attiva@example.com')

    def test_limite_richieste(self):
        for _ in range(8):
            self.client.post(self.lista, {})
        self.assertEqual(self.client.post(self.lista, self.form).status_code, 429)
        self.assertFalse(mail.outbox)

    @override_settings(DEMO_CLEANUP_CRON_TOKEN='token-test')
    def test_pulizia_programmata_richiede_post_autenticato(self):
        richiesta = RichiestaPro.objects.create(
            email='scaduta@example.com', richiesta_il=timezone.now() - timedelta(days=2),
        )
        client = Client(enforce_csrf_checks=True)
        url = reverse('cron_pulisci_candidature')
        self.assertEqual(client.get(url, headers={'Authorization': 'Bearer token-test'}).status_code, 405)
        self.assertEqual(client.post(url, headers={'Authorization': 'Bearer errato'}).status_code, 404)
        self.assertTrue(RichiestaPro.objects.filter(pk=richiesta.pk).exists())
        self.assertEqual(client.post(url, headers={'Authorization': 'Bearer token-test'}).status_code, 204)
        self.assertFalse(RichiestaPro.objects.filter(pk=richiesta.pk).exists())

    def test_errore_email_non_conferma_la_richiesta(self):
        with patch('demo.views.send_mail', return_value=0):
            response = self.client.post(self.lista, self.form)
        self.assertEqual(response.status_code, 503)
        self.assertFalse(RichiestaPro.confermate_attive().exists())
