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
