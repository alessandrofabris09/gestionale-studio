from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase
from studi.models import Studio, ProfiloUtente


class RegistrazioniSicureTests(TestCase):
    strong = 'Vento!7392-Cobalto'

    def payload(self, path, password=None):
        password = self.strong if password is None else password
        data = {'nome_studio': 'Studio QA', 'username': 'qa_registrazione', 'email': 'qa@example.test'}
        if path.startswith('/accounts/'):
            data.update(password1=password, password2=password, accetta_privacy=True, accetta_termini=True)
        else:
            data.update(password=password, conferma_password=password)
        return data

    def test_password_deboli_rifiutate_su_entrambi_percorsi(self):
        for path in ['/utenti/registrazione/', '/accounts/registrazione/']:
            for password in ['12345678', 'abc', 'password']:
                with self.subTest(path=path, password=password):
                    response = self.client.post(path, self.payload(path, password))
                    self.assertEqual(response.status_code, 200)
                    self.assertFalse(User.objects.filter(username='qa_registrazione').exists())

    def test_registrazione_valida_senza_privilegi_globali(self):
        for path in ['/utenti/registrazione/', '/accounts/registrazione/']:
            with self.subTest(path=path):
                data = self.payload(path)
                data['username'] += 'a' if path.startswith('/accounts/') else 'b'
                data['email'] = data['username'] + '@example.test'
                self.client.logout()
                response = self.client.post(path, data)
                self.assertEqual(response.status_code, 302)
                user = User.objects.get(username=data['username'])
                self.assertTrue(user.check_password(self.strong))
                self.assertFalse(user.is_superuser)
                self.assertFalse(user.is_staff)
                profile = ProfiloUtente.objects.get(user=user)
                self.assertEqual(profile.ruolo, 'TITOLARE')
                self.assertEqual(profile.studio.titolare_id, user.pk)
                self.assertEqual(profile.studio.limite_pratiche, 20)

    def test_errore_profilo_non_lascia_account_o_studio(self):
        for path, target in [('/utenti/registrazione/', 'utenti.views.ProfiloUtente.objects.create'), ('/accounts/registrazione/', 'accounts.views.ProfiloUtente.objects.create')]:
            with self.subTest(path=path):
                with patch(target, side_effect=RuntimeError('Errore simulato')):
                    with self.assertRaises(RuntimeError):
                        self.client.post(path, self.payload(path))
                self.assertFalse(User.objects.filter(username='qa_registrazione').exists())
                self.assertFalse(Studio.objects.filter(nome='Studio QA').exists())

    def test_form_nuovi_utenti_rifiutano_password_debole(self):
        from utenti.forms import NuovoUtenteStudioForm as FormA
        from studi.forms import NuovoUtenteStudioForm as FormB
        data = {'username': 'qa_nuovo', 'email': 'nuovo@example.test', 'first_name': 'Nome', 'ruolo': 'TECNICO', 'password': '12345678', 'password1': '12345678', 'password2': '12345678'}
        for cls, field in [(FormA, 'password'), (FormB, 'password1')]:
            with self.subTest(form=cls.__module__):
                form = cls(data)
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_password_simile_username_rifiutata(self):
        from utenti.forms import RegistrazioneStudioForm
        data = self.payload('/utenti/registrazione/', 'qa_registrazione')
        form = RegistrazioneStudioForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)

    def test_creazione_collaboratore_rollback(self):
        owner = User.objects.create_user('qa_owner')
        studio = Studio.objects.create(nome='Esistente', titolare=owner, limite_utenti=5)
        ProfiloUtente.objects.create(user=owner, studio=studio, ruolo='TITOLARE')
        self.client.force_login(owner)
        data = {'username': 'qa_dipendente', 'email': 'dip@example.test', 'first_name': 'Dipendente', 'ruolo': 'TECNICO', 'password': self.strong}
        with patch('utenti.views.ProfiloUtente.objects.create', side_effect=RuntimeError('Errore simulato')):
            with self.assertRaises(RuntimeError):
                self.client.post('/utenti/nuovo/', data)
        self.assertFalse(User.objects.filter(username='qa_dipendente').exists())

    def test_email_duplicata_maiuscole_rifiutata(self):
        from utenti.forms import RegistrazioneStudioForm
        User.objects.create_user('esistente', email='QA@example.test')
        form = RegistrazioneStudioForm(self.payload('/utenti/registrazione/'))
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
