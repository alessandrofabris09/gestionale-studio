from datetime import timedelta
from io import StringIO
from unittest import SkipTest

from django.apps import apps
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

if not apps.is_installed('demo'):
    raise SkipTest('La demo si verifica con gestionale.settings_demo.')

from .models import VERSIONE_CONSENSO, RichiestaPro


class DemoTests(TestCase):
    def test_vecchi_percorsi_rimandano_al_sito_ufficiale(self):
        destinazioni = {
            'demo_home': 'https://studiotecnicocloud.it/',
            'demo_prova': 'https://studiotecnicocloud.it/#funzionalita',
            'demo_lista': 'https://studiotecnicocloud.it/#lancio-beta',
        }
        for nome, destinazione in destinazioni.items():
            with self.subTest(nome=nome):
                for metodo in (self.client.get, self.client.head):
                    response = metodo(reverse(nome), {'richiesta': 'inviata'})
                    self.assertRedirects(response, destinazione, status_code=301, fetch_redirect_response=False)
                    self.assertFalse(response.cookies)
        self.assertEqual(self.client.post(reverse('demo_lista'), {'email': 'studio@example.com'}).status_code, 405)
        self.assertFalse(RichiestaPro.objects.exists())

    def test_link_precedenti_conferma_disattivata_e_revoca_disponibile(self):
        richiesta = RichiestaPro.objects.create(email='studio@example.com', versione_consenso=VERSIONE_CONSENSO)
        conferma = reverse('demo_conferma', args=[richiesta.token])
        revoca = reverse('demo_ritira', args=[richiesta.token_revoca])
        self.assertContains(self.client.get(conferma), 'La beta PRO si è spostata', status_code=410)
        self.assertEqual(self.client.post(conferma).status_code, 410)
        richiesta.refresh_from_db()
        self.assertIsNone(richiesta.confermata_il)
        client = Client(enforce_csrf_checks=True)
        response = client.get(revoca)
        self.assertContains(response, 'Ritira la richiesta')
        self.assertEqual(client.post(revoca).status_code, 403)
        self.assertContains(client.post(revoca, {'csrfmiddlewaretoken': response.cookies['csrftoken'].value}), 'Richiesta rimossa')
        self.assertFalse(RichiestaPro.objects.exists())

    def test_informative_storiche_accessibili(self):
        for nome in ('demo_privacy', 'demo_cookie', 'demo_termini'):
            with self.subTest(nome=nome):
                response = self.client.get(reverse(nome))
                self.assertContains(response, 'name="robots" content="noindex"')
                self.assertFalse(response.cookies)
                self.assertIn("default-src 'self'", response['Content-Security-Policy'])

    def test_pulizia_richieste_precedenti(self):
        now = timezone.now()
        RichiestaPro.objects.create(email='scaduta@example.com', richiesta_il=now - timedelta(days=2))
        RichiestaPro.objects.create(email='vecchia@example.com', confermata_il=now - timedelta(days=366))
        RichiestaPro.objects.create(
            email='attiva@example.com', confermata_il=now, versione_consenso=VERSIONE_CONSENSO,
        )
        call_command('pulisci_lista_pro', stdout=StringIO())
        self.assertEqual(RichiestaPro.objects.get().email, 'attiva@example.com')

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

