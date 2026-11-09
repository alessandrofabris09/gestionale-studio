from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
from zipfile import ZipFile
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.core.management import call_command
from django.core.management.base import CommandError
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from studi.models import Studio
from clienti.models import Cliente
from documenti.models import Documento
from immobili.models import Immobile
from pratiche.models import Pratica
from .views import esegui_backup_database


class BackupAllegatiTests(TestCase):
    def test_ripristino_in_storage_vuoto_e_file_mancante(self):
        user = User.objects.create_user('qa_allegati')
        studio = Studio.objects.create(nome='QA allegati', titolare=user)
        cliente = Cliente.objects.create(studio=studio, nome='QA cliente')
        immobile = Immobile.objects.create(studio=studio, cliente=cliente, comune='QA')
        pratica = Pratica.objects.create(
            studio=studio, cliente=cliente, immobile=immobile, oggetto='QA pratica',
        )
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with override_settings(MEDIA_ROOT=root / 'origine'):
                documento = Documento(pratica=pratica, titolo='QA allegato')
                contenuto = b'allegato fittizio\x00\xff'
                documento.file.save('prova.pdf', ContentFile(contenuto))
                zip_path = root / 'backup.zip'
                call_command('esporta_allegati', zip_path)

                documento.file.storage.delete(documento.file.name)
                with self.assertRaises(CommandError):
                    call_command('esporta_allegati', root / 'incompleto.zip')
                self.assertFalse((root / 'incompleto.zip').exists())

            storage = FileSystemStorage(location=root / 'ripristino')
            with ZipFile(zip_path) as archivio:
                voce, = json.loads(archivio.read('indice.json'))
                self.assertEqual(voce['file'], documento.file.name)
                storage.save(voce['file'], ContentFile(archivio.read(voce['voce_zip'])))
            with storage.open(documento.file.name, 'rb') as ripristinato:
                self.assertEqual(ripristinato.read(), contenuto)


class BackupDatabaseConfiguratoTests(TestCase):
    def test_backup_usa_django_anche_senza_db_sqlite3(self):
        user = User.objects.create_user('qa_backup_reale')
        studio = Studio.objects.create(nome='QA backup', titolare=user)
        cliente = Cliente.objects.create(studio=studio, nome='QA Cliente backup')
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertFalse((root / 'db.sqlite3').exists())
            with override_settings(BASE_DIR=root, MEDIA_ROOT=root / 'media'), patch('backups.views.invia_email_backup') as email:
                result = esegui_backup_database()
                data = json.loads((root / 'backups_files' / result['database']).read_text(encoding='utf-8'))
                self.assertTrue(any(x['model']=='clienti.cliente' and x['pk']==cliente.pk and x['fields']['nome']=='QA Cliente backup' for x in data))
                self.assertTrue((root / 'media' / result['storage_database']).is_file())
                email.assert_called_once()

    def test_backup_riferimenti_permessi_stabili(self):
        from django.contrib.auth.models import Group, Permission
        group = Group.objects.create(name='QA backup permessi')
        permission = Permission.objects.get(content_type__app_label='clienti', codename='view_cliente')
        group.permissions.add(permission)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with override_settings(BASE_DIR=root, MEDIA_ROOT=root / 'media'), patch('backups.views.invia_email_backup'):
                result = esegui_backup_database()
                data = json.loads((root / 'backups_files' / result['database']).read_text(encoding='utf-8'))
                stored = next(x for x in data if x['model']=='auth.group' and x['pk']==group.pk)
                self.assertEqual(stored['fields']['permissions'], [['view_cliente', 'clienti', 'cliente']])
