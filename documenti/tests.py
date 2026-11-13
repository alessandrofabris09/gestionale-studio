from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase
from django.urls import reverse

from clienti.models import Cliente
from immobili.models import Immobile
from pratiche.models import Pratica
from studi.models import ProfiloUtente, Studio

from .models import Documento


class DownloadDocumentiTests(TestCase):
    def test_download_verifica_studio_e_autenticazione(self):
        utenti = {}
        with TemporaryDirectory() as media, self.settings(MEDIA_ROOT=Path(media)):
            for nome in ('alfa', 'beta'):
                utente = User.objects.create_user(nome)
                studio = Studio.objects.create(nome=nome, titolare=utente)
                ProfiloUtente.objects.create(user=utente, studio=studio, ruolo='TITOLARE')
                cliente = Cliente.objects.create(studio=studio, nome=nome)
                immobile = Immobile.objects.create(studio=studio, cliente=cliente, comune='Treviso')
                pratica = Pratica.objects.create(
                    studio=studio, cliente=cliente, immobile=immobile, oggetto=nome,
                )
                documento = Documento(pratica=pratica, titolo=nome)
                documento.file.save(f'{nome}.txt', ContentFile(nome.encode()))
                utenti[nome] = utente, reverse('scarica_documento', args=[documento.pk])

            url = utenti['alfa'][1]
            self.assertEqual(self.client.get(url).status_code, 302)
            for nome, altro in (('alfa', 'beta'), ('beta', 'alfa')):
                utente, url = utenti[nome]
                self.client.force_login(utente)
                self.assertContains(self.client.get(reverse('lista_documenti')), f'href="{url}"')
                with closing(self.client.get(url)) as risposta:
                    self.assertEqual(risposta.status_code, 200)
                    self.assertEqual(b''.join(risposta.streaming_content), nome.encode())
                    self.assertIn('attachment', risposta['Content-Disposition'])
                    self.assertIn('no-store', risposta['Cache-Control'])
                self.assertEqual(self.client.get(utenti[altro][1]).status_code, 404)
