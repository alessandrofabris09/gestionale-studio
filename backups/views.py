import os
import json
import resend

from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.management import call_command
from django.http import FileResponse, Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect

from documenti.models import Documento
from studi.permessi import puo_gestire_backup


MAX_BACKUP_DAYS = 30
CODICE_CRON_BACKUP = 'ABCD1234'


def accesso_negato(request):
    """
    Pagina semplice di blocco accesso.
    """

    return HttpResponseForbidden(
        """
        <h1>Accesso negato</h1>
        <p>Non hai i permessi per accedere a questa sezione.</p>
        <p><a href="/dashboard/">Torna alla dashboard</a></p>
        """
    )


def esegui_backup_database():

    backup_dir = Path(settings.BASE_DIR) / 'backups_files'
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    filename_db = f'backup_database_{timestamp}.json'
    filepath_db = backup_dir / filename_db

    with open(filepath_db, 'w', encoding='utf-8') as file:
        call_command(
            'dumpdata',
            exclude=[
                'auth.permission',
                'contenttypes',
            ],
            stdout=file
        )

    filename_documenti = f'backup_documenti_cloudinary_{timestamp}.json'
    filepath_documenti = backup_dir / filename_documenti

    documenti_backup = []

    for documento in Documento.objects.all().order_by('id'):

        try:
            file_url = documento.file.url
        except Exception:
            file_url = ''

        documenti_backup.append({
            'id': documento.id,
            'titolo': documento.titolo,
            'tipo_documento': documento.tipo_documento,
            'pratica': str(documento.pratica) if documento.pratica else '',
            'file_name': documento.file.name if documento.file else '',
            'file_url': file_url,
            'note': documento.note,
        })

    with open(filepath_documenti, 'w', encoding='utf-8') as file:
        json.dump(
            documenti_backup,
            file,
            ensure_ascii=False,
            indent=4
        )

    pulisci_backup_vecchi(backup_dir)

    invia_email_backup(
        f'{filename_db} + {filename_documenti}'
    )

    return filename_db


@login_required
def lista_backup(request):

    if not puo_gestire_backup(request):
        return accesso_negato(request)

    backup_dir = Path(settings.BASE_DIR) / 'backups_files'
    backup_dir.mkdir(exist_ok=True)

    files = sorted(
        backup_dir.glob('*.json'),
        key=lambda file: file.stat().st_mtime,
        reverse=True
    )

    backups = []

    for file in files:
        backups.append({
            'name': file.name,
            'size': round(file.stat().st_size / 1024, 2),
            'modified': datetime.fromtimestamp(file.stat().st_mtime),
        })

    return render(
        request,
        'backups/lista_backup.html',
        {
            'backups': backups
        }
    )


@login_required
def crea_backup(request):

    if not puo_gestire_backup(request):
        return accesso_negato(request)

    esegui_backup_database()

    return redirect('lista_backup')


def pulisci_backup_vecchi(backup_dir):

    limite = datetime.now() - timedelta(days=MAX_BACKUP_DAYS)

    for file in backup_dir.glob('*.json'):

        data_file = datetime.fromtimestamp(
            file.stat().st_mtime
        )

        if data_file < limite:
            file.unlink()


def invia_email_backup(filename):

    try:
        resend.api_key = os.environ.get('RESEND_API_KEY')

        if not resend.api_key:
            print("ERRORE: RESEND_API_KEY non configurata")
            return

        messaggio_html = f"""
        <div style="font-family:Arial, sans-serif; color:#111827;">
            <h2>Backup database completato</h2>

            <p>
                Il backup del database del Gestionale Studio Tecnico
                è stato creato correttamente.
            </p>

            <table style="border-collapse:collapse;margin-top:20px;">
                <tr>
                    <td style="padding:8px;font-weight:bold;">File backup</td>
                    <td style="padding:8px;">{filename}</td>
                </tr>
                <tr>
                    <td style="padding:8px;font-weight:bold;">Data</td>
                    <td style="padding:8px;">{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</td>
                </tr>
            </table>

            <p style="margin-top:25px;color:#6b7280;font-size:13px;">
                Email generata automaticamente dal Gestionale Studio Tecnico.
            </p>
        </div>
        """

        resend.Emails.send({
            "from": "Gestionale Studio <onboarding@resend.dev>",
            "to": [settings.ALERT_EMAIL],
            "subject": "Backup database completato",
            "html": messaggio_html,
        })

    except Exception as e:
        print(f"ERRORE INVIO EMAIL BACKUP: {e}")


@login_required
def scarica_backup(request, filename):

    if not puo_gestire_backup(request):
        return accesso_negato(request)

    backup_dir = Path(settings.BASE_DIR) / 'backups_files'
    filepath = backup_dir / filename

    if not filepath.exists():
        raise Http404('Backup non trovato')

    return FileResponse(
        open(filepath, 'rb'),
        as_attachment=True,
        filename=filename
    )


def crea_backup_cron(request, codice):

    if codice != CODICE_CRON_BACKUP:
        return HttpResponse(
            'Codice non valido',
            status=403,
            content_type='text/plain'
        )

    try:
        filename = esegui_backup_database()
        messaggio = f'Backup creato correttamente: {filename}'

    except Exception as e:
        messaggio = f'Errore backup: {e}'
        return HttpResponse(
            messaggio,
            status=500,
            content_type='text/plain'
        )

    return HttpResponse(
        messaggio,
        content_type='text/plain'
    )