from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from studi.models import Studio
from clienti.models import Cliente
from .views import esegui_backup_database


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
