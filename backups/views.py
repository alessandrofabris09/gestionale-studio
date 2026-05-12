from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.management import call_command
from django.http import FileResponse, Http404
from django.shortcuts import render, redirect


MAX_BACKUP_DAYS = 30


@login_required
def lista_backup(request):

    if not request.user.is_superuser:
        return redirect('/')

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

    if not request.user.is_superuser:
        return redirect('/')

    backup_dir = Path(settings.BASE_DIR) / 'backups_files'
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    filename = f'backup_database_{timestamp}.json'

    filepath = backup_dir / filename

    with open(filepath, 'w', encoding='utf-8') as file:

        call_command(
            'dumpdata',
            exclude=[
                'auth.permission',
                'contenttypes',
            ],
            stdout=file
        )

    pulisci_backup_vecchi(backup_dir)

    invia_email_backup(filename)

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

        send_mail(
            subject='Backup database completato',
            message=(
                f'Il backup del database è stato creato correttamente.\n\n'
                f'File: {filename}'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ALERT_EMAIL],
            fail_silently=True,
        )

    except Exception:
        pass


@login_required
def scarica_backup(request, filename):

    if not request.user.is_superuser:
        return redirect('/')

    backup_dir = Path(settings.BASE_DIR) / 'backups_files'

    filepath = backup_dir / filename

    if not filepath.exists():
        raise Http404('Backup non trovato')

    return FileResponse(
        open(filepath, 'rb'),
        as_attachment=True,
        filename=filename
    )