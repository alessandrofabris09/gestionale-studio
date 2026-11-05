from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from studi.models import ProfiloUtente, Studio
from studi.utils import is_admin_piattaforma
from .models import Cliente
from .views import lista_clienti


class ClientiIsolamentoTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user_a = User.objects.create_user(username='titolare_a')
        self.user_b = User.objects.create_user(username='titolare_b')
        self.studio_a = Studio.objects.create(nome='A', titolare=self.user_a)
        self.studio_b = Studio.objects.create(nome='B', titolare=self.user_b)
        ProfiloUtente.objects.create(user=self.user_a, studio=self.studio_a, ruolo='TITOLARE')
        ProfiloUtente.objects.create(user=self.user_b, studio=self.studio_b, ruolo='TITOLARE')
        Cliente.objects.create(studio=self.studio_a, nome='Cliente Alfa')
        Cliente.objects.create(studio=self.studio_b, nome='Cliente Beta')

    def lista_per(self, user):
        request = self.factory.get('/clienti/')
        request.user = user
        return lista_clienti(request)

    def test_titolare_non_vede_altri_studi(self):
        risposta = self.lista_per(self.user_a)
        self.assertEqual(risposta.status_code, 200)
        self.assertContains(risposta, 'Cliente Alfa')
        self.assertNotContains(risposta, 'Cliente Beta')

    def test_superuser_collegato_resta_nel_proprio_studio(self):
        self.user_a.is_superuser = True
        self.user_a.save(update_fields=['is_superuser'])
        self.assertFalse(is_admin_piattaforma(self._request(self.user_a)))
        risposta = self.lista_per(self.user_a)
        self.assertContains(risposta, 'Cliente Alfa')
        self.assertNotContains(risposta, 'Cliente Beta')

    def test_admin_piattaforma_senza_profilo(self):
        admin = User.objects.create_superuser(
            username='admin_globale', email='admin@example.test', password='test-only-pass'
        )
        self.assertTrue(is_admin_piattaforma(self._request(admin)))
        risposta = self.lista_per(admin)
        self.assertContains(risposta, 'Cliente Alfa')
        self.assertContains(risposta, 'Cliente Beta')

    def _request(self, user):
        request = self.factory.get('/clienti/')
        request.user = user
        return request
