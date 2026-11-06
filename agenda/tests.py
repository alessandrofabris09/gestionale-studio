from datetime import date

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from studi.models import ProfiloUtente, Studio
from studi.utils import get_studio_utente, is_admin_piattaforma
from agenda.models import EventoAgenda
from agenda.views import get_eventi_queryset
from scadenze.views import get_eventi_agenda_queryset


class IsolamentoStudiTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.owner_a = User.objects.create_user(username='studio_a')
        self.owner_b = User.objects.create_user(username='studio_b')
        self.studio_a = Studio.objects.create(nome='Studio A', titolare=self.owner_a)
        self.studio_b = Studio.objects.create(nome='Studio B', titolare=self.owner_b)
        ProfiloUtente.objects.create(user=self.owner_a, studio=self.studio_a, ruolo='TITOLARE')
        ProfiloUtente.objects.create(user=self.owner_b, studio=self.studio_b, ruolo='TITOLARE')
        self.evento_a = EventoAgenda.objects.create(
            studio=self.studio_a, titolo='Evento A', data=date(2026, 11, 5)
        )
        self.evento_b = EventoAgenda.objects.create(
            studio=self.studio_b, titolo='Evento B', data=date(2026, 11, 5)
        )

    def richiesta(self, user):
        request = self.factory.get('/agenda/')
        request.user = user
        return request

    def test_titolare_vede_solo_il_proprio_studio(self):
        request = self.richiesta(self.owner_a)
        self.assertEqual(list(get_eventi_queryset(request)), [self.evento_a])
        self.assertEqual(list(get_eventi_agenda_queryset(request)), [self.evento_a])

    def test_superuser_con_profilo_non_diventa_globale(self):
        self.owner_a.is_superuser = True
        self.owner_a.save(update_fields=['is_superuser'])
        request = self.richiesta(self.owner_a)
        self.assertFalse(is_admin_piattaforma(request))
        self.assertEqual(list(get_eventi_queryset(request)), [self.evento_a])
        self.assertEqual(list(get_eventi_agenda_queryset(request)), [self.evento_a])

    def test_admin_piattaforma_non_eredita_primo_studio(self):
        admin = User.objects.create_superuser(
            username='admin_piattaforma', email='admin@example.test', password='test-only-pass'
        )
        request = self.richiesta(admin)
        self.assertIsNone(get_studio_utente(request))
        self.assertTrue(is_admin_piattaforma(request))
        self.assertEqual(get_eventi_queryset(request).count(), 2)


class EmailManualiProtezioneTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        from studi.models import Studio, ProfiloUtente
        self.user = User.objects.create_user('qa_email_manuale')
        self.studio = Studio.objects.create(nome='QA email', titolare=self.user)
        self.profile = ProfiloUtente.objects.create(user=self.user, studio=self.studio, ruolo='TITOLARE')
        self.client.force_login(self.user)

    def test_get_non_invia_email(self):
        from unittest.mock import patch
        with patch('agenda.views.invia_email_agenda_giornaliera') as agenda, patch('scadenze.views.invia_email_scadenze_leggera') as scadenze, patch('scadenze.views.invia_email_agenda_giornaliera') as combined:
            for path in ['/agenda/invia-email/', '/scadenze/invia-alert-email/', '/scadenze/invia-alert-giornalieri/']:
                with self.subTest(path=path):
                    self.assertEqual(self.client.get(path).status_code, 405)
            agenda.assert_not_called()
            scadenze.assert_not_called()
            combined.assert_not_called()

    def test_post_scoped_e_csrf(self):
        from unittest.mock import patch
        from django.test import Client
        with patch('scadenze.views.invia_email_scadenze_leggera', return_value='Simulata') as scadenze, patch('scadenze.views.invia_email_agenda_giornaliera', return_value='Simulata') as agenda:
            self.assertEqual(self.client.post('/scadenze/invia-alert-giornalieri/').status_code, 200)
            scadenze.assert_called_once_with(self.studio)
            agenda.assert_called_once_with(self.studio)
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.user)
        self.assertEqual(strict.post('/scadenze/invia-alert-giornalieri/').status_code, 403)

    def test_collaboratore_bloccato(self):
        from unittest.mock import patch
        self.profile.ruolo = 'COLLABORATORE'
        self.profile.save()
        with patch('scadenze.views.invia_email_scadenze_leggera') as send:
            self.assertEqual(self.client.post('/scadenze/invia-alert-email/').status_code, 403)
            send.assert_not_called()


    def test_messaggi_multiriga_leggibili_e_html_escapato(self):
        from unittest.mock import patch
        with patch('scadenze.views.invia_email_scadenze_leggera', return_value='<script>esempio</script>'), patch('scadenze.views.invia_email_agenda_giornaliera', return_value='Seconda riga'):
            response = self.client.post('/scadenze/invia-alert-giornalieri/')
            self.assertContains(response, '&lt;script&gt;esempio&lt;/script&gt;<br>Seconda riga')
            self.assertNotContains(response, '<script>esempio</script>')
