from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import Client, TestCase
from studi.models import Studio, ProfiloUtente


class BackupUnificatoTests(TestCase):
    def test_vecchio_indirizzo_apre_backup_principale(self):
        user = User.objects.create_superuser('qa_backup', '', 'Solo-qa-829!')
        self.client.force_login(user)
        with patch('backups.views.esegui_backup_database') as backup:
            for method in [self.client.get, self.client.post]:
                response = method('/dashboard/backup/')
                self.assertRedirects(response, '/backups/', fetch_redirect_response=False)
            backup.assert_not_called()

    def test_titolare_non_accede_backup_storico(self):
        user = User.objects.create_user('qa_owner_backup')
        studio = Studio.objects.create(nome='QA', titolare=user)
        ProfiloUtente.objects.create(user=user, studio=studio, ruolo='TITOLARE')
        self.client.force_login(user)
        self.assertEqual(self.client.get('/dashboard/backup/').status_code, 403)
