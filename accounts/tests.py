import re
from urllib.parse import urlsplit

from django.contrib.auth.models import User
from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse


class RecuperoPasswordTests(TestCase):
    def test_link_monouso_e_risposta_neutra(self):
        client = Client(enforce_csrf_checks=True)

        def invia_modulo(path, dati):
            form = client.get(path, secure=True)
            self.assertContains(form, '<meta name="referrer" content="same-origin">', html=True)
            return client.post(path, {
                **dati, 'csrfmiddlewaretoken': client.cookies['csrftoken'].value,
            }, secure=True, HTTP_REFERER=f'https://testserver{path}')

        user = User.objects.create_user('recupero_qa', 'qa@example.test', 'Vecchia-QA-123!')
        endpoint = reverse('password_reset')
        for email in ('sconosciuto@example.test', user.email):
            self.assertRedirects(
                invia_modulo(endpoint, {'email': email}),
                reverse('password_reset_done'),
            )
        self.assertEqual(len(mail.outbox), 1)
        url = re.search(r'https?://\S+', mail.outbox[0].body).group()
        self.assertEqual(urlsplit(url).scheme, 'https')
        link = urlsplit(url).path
        form = client.get(link, secure=True)
        nuova = 'Nuova-QA-sicura-987!'
        self.assertRedirects(
            invia_modulo(form['Location'], {'new_password1': nuova, 'new_password2': nuova}),
            reverse('password_reset_complete'),
        )
        user.refresh_from_db()
        self.assertTrue(user.check_password(nuova))
        self.assertContains(client.get(link, secure=True), 'Il link è scaduto o è già stato usato.')
