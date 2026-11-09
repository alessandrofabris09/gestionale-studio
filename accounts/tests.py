from django.test import TestCase

# Create your tests here.
import re
from urllib.parse import urlsplit

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse


class RecuperoPasswordTests(TestCase):
    def test_link_monouso_e_risposta_neutra(self):
        user = User.objects.create_user('recupero_qa', 'qa@example.test', 'Vecchia-QA-123!')
        endpoint = reverse('password_reset')
        for email in ('sconosciuto@example.test', user.email):
            self.assertRedirects(
                self.client.post(endpoint, {'email': email}),
                reverse('password_reset_done'),
            )
        self.assertEqual(len(mail.outbox), 1)
        url = re.search(r'https?://\S+', mail.outbox[0].body).group()
        link = urlsplit(url).path
        form = self.client.get(link)
        nuova = 'Nuova-QA-sicura-987!'
        self.assertRedirects(
            self.client.post(form['Location'], {'new_password1': nuova, 'new_password2': nuova}),
            reverse('password_reset_complete'),
        )
        user.refresh_from_db()
        self.assertTrue(user.check_password(nuova))
        self.assertContains(self.client.get(link), 'Il link è scaduto o è già stato usato.')
