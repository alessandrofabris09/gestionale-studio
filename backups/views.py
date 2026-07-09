import os
import json
import resend

from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.base import File
from django.core.files.storage import default_storage
from django.core.management import call_command
from django.http import HttpResponse, Http404, FileResponse
from django.shortcuts import render, redirect
from django.core.files.storage import default_storage

from documenti.models import Documento
from studi.permessi import puo_gestire_backup
from studi.email_templates import layout_email_base, tabella_email


MAX_BACKUP_DAYS = int(
    os.environ.get(
        'MAX_BACKUP_DAYS',
        30
    )
)


CODICE_CRON_BACKUP = os.environ.get(
    'CODICE_CRON_BACKUP',
    ''
)


def accesso_negato(request):
    """
    Pagina grafica di blocco accesso.
    """

    return render(
        request,
        'errors/accesso_negato.html',
        status=403
    )


def get_backup_dir():
    """
    Cartella locale temporanea dei backup.

    Attenzione:
    su Render questa cartella non va considerata archivio definitivo,
    perché il filesystem può essere temporaneo se non hai un persistent disk.

    L'archivio definitivo dei backup viene caricato su Backblaze B2
    tramite default_storage.
    """

    backup_dir = Path(settings.BASE_DIR) / 'backups_files'
    backup_dir.mkdir(exist_ok=True)

    return backup_dir


def carica_backup_su_storage(filepath, filename, sottocartella):
    """
    Carica un file di backup nello storage Django configurato.

    Se USE_BACKBLAZE_B2=True, viene caricato su Backblaze B2.
    Se USE_BACKBLAZE_B2=False, viene salvato nello storage locale.

    Struttura prevista:
    backups/database/
    backups/documenti_storage/
    """

    storage_path = f'backups/{sottocartella}/{filename}'

    with open(filepath, 'rb') as file:

        if default_storage.exists(storage_path):
            default_storage.delete(storage_path)

        saved_path = default_storage.save(
            storage_path,
            File(file)
        )

    try:
        file_url = default_storage.url(saved_path)
    except Exception:
        file_url = ''

    return {
        'path': saved_path,
        'url': file_url,
    }


def esegui_backup_database():
    """
    Esegue un backup tecnico globale del database e dei riferimenti documenti.

    Il backup documenti NON scarica fisicamente i file da Backblaze B2.
    Salva solo i metadati e i riferimenti storage dei documenti caricati.

    Crea:
    - copia locale temporanea su Render in backups_files/
    - copia definitiva su Backblaze B2 in backups/database/
    - copia definitiva su Backblaze B2 in backups/documenti_storage/
    """

    backup_dir = get_backup_dir()

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    # =========================
    # BACKUP DATABASE
    # =========================

    filename_db = f'backup_database_{timestamp}.json'
    filepath_db = backup_dir / filename_db

    with open(filepath_db, 'w', encoding='utf-8') as file:

        call_command(
            'dumpdata',
            exclude=[
                'auth.permission',
                'contenttypes',
                'sessions.session',
            ],
            stdout=file
        )

    # =========================
    # BACKUP RIFERIMENTI DOCUMENTI
    # =========================

    filename_documenti = f'backup_documenti_storage_{timestamp}.json'
    filepath_documenti = backup_dir / filename_documenti

    documenti_backup = []

    for documento in Documento.objects.all().order_by('id'):

        try:
            file_url = documento.file.url
        except Exception:
            file_url = ''

        try:
            file_name = documento.file.name
        except Exception:
            file_name = ''

        documenti_backup.append({
            'id': documento.id,
            'titolo': documento.titolo,
            'tipo_documento': documento.tipo_documento,
            'pratica_id': documento.pratica.id if documento.pratica else None,
            'pratica': str(documento.pratica) if documento.pratica else '',
            'studio_id': (
                documento.pratica.studio.id
                if documento.pratica and documento.pratica.studio
                else None
            ),
            'studio': (
                documento.pratica.studio.nome
                if documento.pratica and documento.pratica.studio
                else ''
            ),
            'file_name': file_name,
            'file_url': file_url,
            'note': documento.note,
            'caricato_il': (
                documento.caricato_il.strftime('%d/%m/%Y %H:%M:%S')
                if documento.caricato_il
                else ''
            ),
            'storage_provider': (
                'Backblaze B2'
                if getattr(settings, 'USE_BACKBLAZE_B2', False)
                else 'FileSystem locale'
            ),
        })

    with open(filepath_documenti, 'w', encoding='utf-8') as file:

        json.dump(
            documenti_backup,
            file,
            ensure_ascii=False,
            indent=4
        )

    # =========================
    # CARICAMENTO SU BACKBLAZE / STORAGE
    # =========================

    storage_db = carica_backup_su_storage(
        filepath=filepath_db,
        filename=filename_db,
        sottocartella='database'
    )

    storage_documenti = carica_backup_su_storage(
        filepath=filepath_documenti,
        filename=filename_documenti,
        sottocartella='documenti_storage'
    )

    # =========================
    # PULIZIA BACKUP LOCALI VECCHI
    # =========================

    pulisci_backup_vecchi(backup_dir)

    # =========================
    # EMAIL TECNICA
    # =========================

    invia_email_backup(
        filename_db=filename_db,
        filename_documenti=filename_documenti,
        totale_documenti=len(documenti_backup),
        storage_db=storage_db,
        storage_documenti=storage_documenti,
    )

    return {
        'database': filename_db,
        'documenti': filename_documenti,
        'totale_documenti': len(documenti_backup),
        'storage_database': storage_db.get('path', ''),
        'storage_documenti': storage_documenti.get('path', ''),
    }


@login_required
def lista_backup(request):
    """
    Lista backup tecnici locali temporanei presenti su Render.

    La copia definitiva viene salvata su Backblaze B2.
    """

    if not puo_gestire_backup(request):
        return accesso_negato(request)

    backup_dir = get_backup_dir()

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
    """
    Crea backup manuale.

    Usa la stessa procedura del cron:
    - backup locale temporaneo su Render
    - backup definitivo su Backblaze B2
    - email tecnica di conferma
    """

    if not puo_gestire_backup(request):
        return accesso_negato(request)

    esegui_backup_database()

    return redirect('lista_backup')


def pulisci_backup_vecchi(backup_dir):
    """
    Elimina i backup locali temporanei più vecchi di MAX_BACKUP_DAYS.

    Questa pulizia riguarda solo la cartella backups_files su Render.
    Non elimina i backup presenti su Backblaze B2.
    """

    limite = datetime.now() - timedelta(days=MAX_BACKUP_DAYS)

    for file in backup_dir.glob('*.json'):

        data_file = datetime.fromtimestamp(
            file.stat().st_mtime
        )

        if data_file < limite:

            try:
                file.unlink()
            except Exception:
                pass


def invia_email_backup(
    filename_db,
    filename_documenti,
    totale_documenti,
    storage_db=None,
    storage_documenti=None
):
    """
    Invia una email tecnica sull'esito del backup.
    """

    try:

        resend.api_key = os.environ.get(
            'RESEND_API_KEY'
        )

        if not resend.api_key:
            print('ERRORE: RESEND_API_KEY non configurata')
            return

        if not settings.ALERT_EMAIL:
            print('ERRORE: ALERT_EMAIL non configurata')
            return

        storage_db = storage_db or {}
        storage_documenti = storage_documenti or {}

        storage_provider = (
            'Backblaze B2'
            if getattr(settings, 'USE_BACKBLAZE_B2', False)
            else 'FileSystem locale'
        )

        righe = [
            [
                'Esito backup',
                'Completato correttamente',
            ],
            [
                'Backup database',
                filename_db,
            ],
            [
                'Percorso database',
                storage_db.get('path', '-'),
            ],
            [
                'Backup riferimenti documenti',
                filename_documenti,
            ],
            [
                'Percorso riferimenti documenti',
                storage_documenti.get('path', '-'),
            ],
            [
                'Documenti censiti',
                totale_documenti,
            ],
            [
                'Data esecuzione',
                datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            ],
            [
                'Storage backup definitivo',
                storage_provider,
            ],
            [
                'Copia locale temporanea',
                'Render / backups_files/',
            ],
        ]

        tabella = tabella_email(
            headers=[
                'Voce',
                'Dettaglio',
            ],
            rows=righe
        )

        contenuto_html = f"""
        <p style="font-size:16px;line-height:1.6;margin:0;color:#374151;">
            Il backup tecnico globale del gestionale è stato eseguito correttamente.
        </p>

        <div style="
            margin-top:24px;
            background:#f9fafb;
            border:1px solid #e5e7eb;
            border-radius:14px;
            padding:18px 20px;
        ">
            <div style="font-size:14px;color:#6b7280;font-weight:bold;text-transform:uppercase;letter-spacing:0.06em;">
                Backup tecnico
            </div>

            <div style="font-size:28px;font-weight:bold;color:#111827;margin-top:6px;">
                Completato
            </div>

            <div style="font-size:15px;color:#6b7280;margin-top:4px;">
                Database + riferimenti documenti storage
            </div>
        </div>

        {tabella}

        <p style="font-size:13px;line-height:1.5;margin-top:22px;color:#6b7280;">
            Nota: il backup riferimenti documenti salva i metadati e i percorsi
            dei file caricati, ma non duplica fisicamente i documenti già presenti
            nello storage.
        </p>
        """

        messaggio_html = layout_email_base(
            titolo='Backup tecnico completato',
            sottotitolo='Riepilogo automatico del backup globale della piattaforma.',
            contenuto_html=contenuto_html,
        )

        resend.Emails.send({
            "from": settings.EMAIL_FROM_NOTIFICHE,
            "to": [settings.ALERT_EMAIL],
            "subject": "Backup tecnico completato - Studio Tecnico Cloud",
            "html": messaggio_html,
            "text": (
                "Backup tecnico completato. "
                f"Database: {filename_db}. "
                f"Percorso database: {storage_db.get('path', '-')}. "
                f"Documenti: {filename_documenti}. "
                f"Percorso documenti: {storage_documenti.get('path', '-')}. "
                f"Totale documenti censiti: {totale_documenti}."
            ),
        })

    except Exception as e:

        print(f'ERRORE INVIO EMAIL BACKUP: {e}')


@login_required
def scarica_backup(request, filename):
    """
    Scarica un file di backup locale temporaneo.

    La funzione resta disponibile, anche se al momento non la usi.
    """

    if not puo_gestire_backup(request):
        return accesso_negato(request)

    backup_dir = get_backup_dir()
    filepath = backup_dir / filename

    if not filepath.exists():
        raise Http404('Backup non trovato')

    return FileResponse(
        open(filepath, 'rb'),
        as_attachment=True,
        filename=filename
    )


def info_storage_backup():
    """
    Restituisce informazioni tecniche sullo storage effettivamente usato.
    Serve per capire se il backup sta andando su Backblaze o su filesystem locale.
    """

    return {
        'use_backblaze_b2': getattr(settings, 'USE_BACKBLAZE_B2', False),
        'storage_class': f'{default_storage.__class__.__module__}.{default_storage.__class__.__name__}',
        'bucket': getattr(settings, 'AWS_STORAGE_BUCKET_NAME', ''),
        'endpoint': getattr(settings, 'AWS_S3_ENDPOINT_URL', ''),
    }


def crea_backup_cron(request, codice):
    """
    Endpoint cron per backup tecnico.

    Usato da cron-job.org.
    """

    if not CODICE_CRON_BACKUP:

        return HttpResponse(
            'CODICE_CRON_BACKUP non configurato',
            status=403,
            content_type='text/plain'
        )

    if codice != CODICE_CRON_BACKUP:

        return HttpResponse(
            'Codice non valido',
            status=403,
            content_type='text/plain'
        )

    try:

        risultato = esegui_backup_database()
        storage_info = info_storage_backup()

        messaggio = (
            'Backup creato correttamente.\n'
            f"Database: {risultato['database']}\n"
            f"Storage database: {risultato['storage_database']}\n"
            f"Documenti: {risultato['documenti']}\n"
            f"Storage documenti: {risultato['storage_documenti']}\n"
            f"Totale documenti: {risultato['totale_documenti']}\n"
            '\n'
            'INFO STORAGE:\n'
            f"USE_BACKBLAZE_B2: {storage_info['use_backblaze_b2']}\n"
            f"STORAGE CLASS: {storage_info['storage_class']}\n"
            f"BUCKET: {storage_info['bucket']}\n"
            f"ENDPOINT: {storage_info['endpoint']}\n"
        )

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