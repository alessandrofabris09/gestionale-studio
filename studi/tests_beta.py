import json
from datetime import date, timedelta
from io import BytesIO, StringIO
from unittest.mock import patch
from zipfile import ZipFile

from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from clienti.models import Cliente
from documenti.models import Documento
from immobili.models import Immobile
from pratiche.models import Pratica

from .beta_pro import attiva_beta_pro
from .models import BetaStudio, ProfiloUtente, Studio


class BetaStudioTests(TestCase):
    @override_settings(BETA_REMINDER_CRON_TOKEN='token-test')
    def test_promemoria_programmato_riporta_errori_senza_esporre_dettagli(self):
        client = Client(enforce_csrf_checks=True)
        url = reverse('cron_avvisa_scadenza_beta')
        with patch('gestionale.cron.call_command', side_effect=[CommandError('dettagli interni'), None]) as comando:
            self.assertEqual(client.post(url).status_code, 404)
            comando.assert_not_called()
            with self.assertLogs('gestionale.cron', level='ERROR'):
                errore = client.post(url, headers={'Authorization': 'Bearer token-test'})
            self.assertEqual(errore.status_code, 503)
            self.assertEqual(errore.content, b'')
            self.assertEqual(client.post(url, headers={'Authorization': 'Bearer token-test'}).status_code, 204)
            self.assertEqual(comando.call_count, 2)
            self.assertEqual(comando.call_args.args, ('avvisa_scadenza_beta',))

    def crea_studio(self, nome):
        utente = User.objects.create_user(nome, email=f'{nome}@example.test')
        studio = Studio.objects.create(nome=nome, titolare=utente)
        ProfiloUtente.objects.create(user=utente, studio=studio, ruolo='TITOLARE')
        return studio

    def setUp(self):
        cache.clear()
        self.studio = self.crea_studio('beta')
        self.altro = self.crea_studio('altro')
        self.url_abbonamento = reverse('abbonamento')

    def crea_pratica(self, studio):
        cliente = Cliente.objects.create(studio=studio, nome=f'Cliente {studio.nome}')
        immobile = Immobile.objects.create(studio=studio, cliente=cliente, comune='Comune fittizio')
        return Pratica.objects.create(studio=studio, cliente=cliente, immobile=immobile, oggetto='Pratica fittizia')

    def sposta_scadenza(self, giorni):
        oggi = timezone.localdate()
        BetaStudio.objects.filter(studio=self.studio).update(
            attivata_il=oggi - timedelta(days=190),
            fine_pro_il=oggi + timedelta(days=giorni),
            fine_esportazione_il=oggi + timedelta(days=giorni + 30),
        )

    def test_assegnazione_unica_date_e_limite(self):
        with patch('studi.beta_pro.timezone.localdate', return_value=date(2027, 8, 31)):
            beta, creata = attiva_beta_pro(self.studio.pk)
            self.assertTrue(creata)
            self.assertEqual(beta.fine_pro_il, date(2028, 2, 29))
            self.assertEqual(beta.fine_esportazione_il, date(2028, 3, 30))
            self.assertEqual(attiva_beta_pro(self.studio.pk), (beta, False))
        BetaStudio.objects.bulk_create([
            BetaStudio(posto=posto, attivata_il=beta.attivata_il, fine_pro_il=beta.fine_pro_il,
                       fine_esportazione_il=beta.fine_esportazione_il)
            for posto in range(2, 16)
        ])
        with self.assertRaises(ValidationError):
            attiva_beta_pro(self.altro.pk)

    def test_rifiuta_pro_e_checkout_in_corso(self):
        Studio.objects.filter(pk=self.studio.pk).update(piano='PRO')
        with self.assertRaises(ValidationError):
            attiva_beta_pro(self.studio.pk)
        Studio.objects.filter(pk=self.studio.pk).update(piano='FREE', stripe_checkout_pending={'id': 'test'})
        with self.assertRaises(ValidationError):
            attiva_beta_pro(self.studio.pk)

    def test_azione_admin_riservata_e_idempotente(self):
        url = reverse('admin:studi_studio_changelist')
        dati = {'action': 'ammetti_alla_beta', '_selected_action': [self.studio.pk], 'index': 0}
        self.client.force_login(self.studio.titolare)
        self.assertEqual(self.client.post(url, dati).status_code, 302)
        self.assertFalse(BetaStudio.objects.exists())
        admin = User.objects.create_superuser('piattaforma', email='admin@example.test', password='test')
        self.client.force_login(admin)
        self.assertEqual(self.client.post(url, dati).status_code, 302)
        self.client.post(url, dati)
        self.assertEqual(BetaStudio.objects.filter(studio=self.studio).count(), 1)

    def test_sola_lettura_blocca_scritture_e_scade(self):
        attiva_beta_pro(self.studio.pk)
        pratica = self.crea_pratica(self.studio)
        self.client.force_login(self.studio.titolare)
        self.assertContains(self.client.get(self.url_abbonamento), '500 MB')
        self.assertNotContains(self.client.get(self.url_abbonamento), 'checkout')
        self.sposta_scadenza(0)
        self.assertEqual(self.client.get(reverse('dettaglio_pratica', args=[pratica.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('modifica_pratica', args=[pratica.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse('elimina_pratica', args=[pratica.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse('checkout_pro')).status_code, 403)
        self.assertTrue(Pratica.objects.filter(pk=pratica.pk).exists())
        self.sposta_scadenza(-30)
        self.assertEqual(self.client.get(reverse('dettaglio_pratica', args=[pratica.pk])).status_code, 403)
        self.assertContains(self.client.get(self.url_abbonamento), 'periodo di consultazione della beta è terminato')
        Studio.objects.filter(pk=self.studio.pk).update(piano='PRO', stato_abbonamento='ATTIVO')
        self.assertEqual(self.client.get(reverse('dettaglio_pratica', args=[pratica.pk])).status_code, 200)

    def test_quota_beta_per_upload_singolo_e_multiplo(self):
        attiva_beta_pro(self.studio.pk)
        pratica = self.crea_pratica(self.studio)
        self.client.force_login(self.studio.titolare)
        file = SimpleUploadedFile('prova.pdf', b'contenuto')
        with patch('studi.utils.studio_storage_usato_mb', return_value=500):
            risposta = self.client.post(reverse('carica_documento', args=[pratica.pk]), {
                'file': file, 'titolo': 'Allegato', 'tipo_documento': 'ALTRO',
            })
            self.assertContains(risposta, '500 MB', status_code=403)
            risposta = self.client.post(reverse('carica_documenti_multipli', args=[pratica.pk]), {
                'files': [SimpleUploadedFile('altro.pdf', b'altro')], 'tipo_documento': 'ALTRO',
            })
            self.assertEqual(risposta.status_code, 403)
        self.assertFalse(Documento.objects.exists())
        risposta = self.client.post(reverse('carica_documento', args=[pratica.pk]), {
            'file': SimpleUploadedFile('prova.pdf', b'contenuto'), 'titolo': 'Allegato', 'tipo_documento': 'ALTRO',
        })
        self.assertEqual(risposta.status_code, 302)
        self.assertEqual(Documento.objects.count(), 1)

    def test_archivio_privato_titolare_e_isolamento(self):
        attiva_beta_pro(self.studio.pk)
        self.sposta_scadenza(0)
        documento = Documento(pratica=self.crea_pratica(self.studio), titolo='Allegato')
        documento.file.save('beta.pdf', ContentFile(b'finto beta'))
        esterno = Documento(pratica=self.crea_pratica(self.altro), titolo='Altro')
        esterno.file.save('altro.pdf', ContentFile(b'finto altro'))
        url = reverse('esporta_beta')
        self.client.force_login(self.altro.titolare)
        self.assertEqual(self.client.post(url).status_code, 403)
        tecnico = User.objects.create_user('tecnico')
        ProfiloUtente.objects.create(user=tecnico, studio=self.studio, ruolo='TECNICO')
        self.client.force_login(tecnico)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.client.force_login(self.studio.titolare)
        self.assertEqual(self.client.get(url).status_code, 405)
        risposta = self.client.post(url)
        self.assertEqual(risposta.status_code, 200)
        self.assertIn('no-store', risposta['Cache-Control'])
        with ZipFile(BytesIO(b''.join(risposta.streaming_content))) as archivio:
            self.assertEqual(archivio.read(f'allegati/{documento.pk}'), b'finto beta')
            self.assertNotIn(f'allegati/{esterno.pk}', archivio.namelist())
            dati = json.loads(archivio.read('dati-operativi.json'))
            self.assertFalse(any(riga['model'] == 'documenti.documento' and riga['pk'] == esterno.pk for riga in dati))
        self.sposta_scadenza(-30)
        self.assertEqual(self.client.post(url).status_code, 403)

    def test_promemoria_una_volta_e_riprova_dopo_errore(self):
        attiva_beta_pro(self.studio.pk)
        self.sposta_scadenza(31)
        call_command('avvisa_scadenza_beta', stdout=StringIO())
        self.assertFalse(mail.outbox)
        self.sposta_scadenza(30)
        with patch('studi.management.commands.avvisa_scadenza_beta.send_mail', return_value=0):
            with self.assertRaises(CommandError):
                call_command('avvisa_scadenza_beta', stdout=StringIO())
        self.assertIsNone(BetaStudio.objects.get(studio=self.studio).avvisata_il)
        call_command('avvisa_scadenza_beta', stdout=StringIO())
        call_command('avvisa_scadenza_beta', stdout=StringIO())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.studio.titolare.email])
