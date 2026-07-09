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

    Layout grafico uniforme tipo "Sistema Backup":
    - testata viola
    - stato OK verde
    - tabella dettagli
    - messaggio tecnico finale
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

        data_esecuzione = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        percorso_database = storage_db.get(
            'path',
            '-'
        )

        percorso_documenti = storage_documenti.get(
            'path',
            '-'
        )

        contenuto_html = f"""
        <div style="
            background:#f3f4f6;
            padding:0;
            margin:0;
            font-family:Arial, sans-serif;
            color:#111827;
        ">

            <div style="
                max-width:720px;
                margin:0 auto;
                background:white;
                border-radius:0 0 18px 18px;
                overflow:hidden;
                box-shadow:0 8px 24px rgba(0,0,0,0.08);
            ">

                <div style="
                    background:linear-gradient(135deg,#4f46e5,#7c3aed);
                    color:white;
                    padding:30px 34px;
                ">

                    <div style="
                        font-size:12px;
                        font-weight:bold;
                        text-transform:uppercase;
                        letter-spacing:0.08em;
                        opacity:0.9;
                        margin-bottom:8px;
                    ">
                        Studio Tecnico Cloud
                    </div>

                    <div style="
                        font-size:28px;
                        font-weight:900;
                        line-height:1.2;
                        margin-bottom:8px;
                    ">
                        Sistema Backup
                    </div>

                    <div style="
                        font-size:14px;
                        font-weight:bold;
                        opacity:0.95;
                    ">
                        Notifica automatica di sicurezza e continuità operativa
                    </div>

                </div>

                <div style="
                    padding:34px;
                ">

                    <div style="
                        display:flex;
                        align-items:flex-start;
                        gap:18px;
                        margin-bottom:28px;
                    ">

                        <div style="
                            width:42px;
                            height:42px;
                            border-radius:999px;
                            background:#dcfce7;
                            color:#166534;
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            font-size:14px;
                            font-weight:900;
                            flex-shrink:0;
                            text-align:center;
                            line-height:42px;
                        ">
                            OK
                        </div>

                        <div>
                            <div style="
                                font-size:22px;
                                font-weight:900;
                                color:#111827;
                                margin-bottom:8px;
                            ">
                                Backup completato correttamente
                            </div>

                            <div style="
                                font-size:15px;
                                color:#4b5563;
                                line-height:1.6;
                            ">
                                Il backup automatico di Studio Tecnico Cloud è stato eseguito
                                e archiviato correttamente.
                            </div>
                        </div>

                    </div>

                    <div style="
                        border:1px solid #d1d5db;
                        border-radius:16px;
                        overflow:hidden;
                        margin-top:22px;
                        margin-bottom:28px;
                    ">

                        <div style="
                            padding:18px 20px;
                            background:#f9fafb;
                            font-size:15px;
                            font-weight:900;
                            color:#111827;
                            border-bottom:1px solid #e5e7eb;
                        ">
                            Dettagli del backup
                        </div>

                        <table style="
                            width:100%;
                            border-collapse:collapse;
                            font-size:14px;
                        ">

                            <tr>
                                <td style="
                                    width:34%;
                                    padding:14px 20px;
                                    color:#6b7280;
                                    border-bottom:1px solid #e5e7eb;
                                    vertical-align:top;
                                ">
                                    Stato
                                </td>
                                <td style="
                                    padding:14px 20px;
                                    color:#111827;
                                    border-bottom:1px solid #e5e7eb;
                                    vertical-align:top;
                                    font-weight:bold;
                                ">
                                    <span style="
                                        display:inline-block;
                                        background:#dcfce7;
                                        color:#166534;
                                        padding:6px 14px;
                                        border-radius:999px;
                                        font-size:12px;
                                        font-weight:900;
                                        letter-spacing:0.03em;
                                    ">
                                        COMPLETATO
                                    </span>
                                </td>
                            </tr>

                            <tr>
                                <td style="
                                    padding:14px 20px;
                                    color:#6b7280;
                                    border-bottom:1px solid #e5e7eb;
                                    vertical-align:top;
                                ">
                                    Data e ora
                                </td>
                                <td style="
                                    padding:14px 20px;
                                    color:#111827;
                                    border-bottom:1px solid #e5e7eb;
                                    vertical-align:top;
                                ">
                                    {data_esecuzione}
                                </td>
                            </tr>

                            <tr>
                                <td style="
                                    padding:14px 20px;
                                    color:#6b7280;
                                    border-bottom:1px solid #e5e7eb;
                                    vertical-align:top;
                                ">
                                    Backup database
                                </td>
                                <td style="
                                    padding:14px 20px;
                                    color:#111827;
                                    border-bottom:1px solid #e5e7eb;
                                    vertical-align:top;
                                    word-break:break-word;
                                ">
                                    {filename_db}
                                </td>
                            </tr>

                            <tr>
                                <td style="
                                    padding:14px 20px;
                                    color:#6b7280;
                                    border-bottom:1px solid #e5e7eb;
                                    vertical-align:top;
                                ">
                                    Backup riferimenti documenti
                                </td>
                                <td style="
                                    padding:14px 20px;
                                    color:#111827;
                                    border-bottom:1px solid #e5e7eb;
                                    vertical-align:top;
                                    word-break:break-word;
                                ">
                                    {filename_documenti}
                                </td>
                            </tr>

                            <tr>
                                <td style="
                                    padding:14px 20px;
                                    color:#6b7280;
                                    border-bottom:1px solid #e5e7eb;
                                    vertical-align:top;
                                ">
                                    Documenti censiti
                                </td>
                                <td style="
                                    padding:14px 20px;
                                    color:#111827;
                                    border-bottom:1px solid #e5e7eb;
                                    vertical-align:top;
                                ">
                                    {totale_documenti}
                                </td>
                            </tr>

                            <tr>
                                <td style="
                                    padding:14px 20px;
                                    color:#6b7280;
                                    border-bottom:1px solid #e5e7eb;
                                    vertical-align:top;
                                ">
                                    Archivio definitivo
                                </td>
                                <td style="
                                    padding:14px 20px;
                                    color:#111827;
                                    border-bottom:1px solid #e5e7eb;
                                    vertical-align:top;
                                ">
                                    {storage_provider}
                                </td>
                            </tr>

                            <tr>
                                <td style="
                                    padding:14px 20px;
                                    color:#6b7280;
                                    border-bottom:1px solid #e5e7eb;
                                    vertical-align:top;
                                ">
                                    Percorso database
                                </td>
                                <td style="
                                    padding:14px 20px;
                                    color:#111827;
                                    border-bottom:1px solid #e5e7eb;
                                    vertical-align:top;
                                    word-break:break-word;
                                ">
                                    {percorso_database}
                                </td>
                            </tr>

                            <tr>
                                <td style="
                                    padding:14px 20px;
                                    color:#6b7280;
                                    border-bottom:1px solid #e5e7eb;
                                    vertical-align:top;
                                ">
                                    Percorso riferimenti documenti
                                </td>
                                <td style="
                                    padding:14px 20px;
                                    color:#111827;
                                    border-bottom:1px solid #e5e7eb;
                                    vertical-align:top;
                                    word-break:break-word;
                                ">
                                    {percorso_documenti}
                                </td>
                            </tr>

                            <tr>
                                <td style="
                                    padding:14px 20px;
                                    color:#6b7280;
                                    vertical-align:top;
                                ">
                                    Copia temporanea
                                </td>
                                <td style="
                                    padding:14px 20px;
                                    color:#111827;
                                    vertical-align:top;
                                ">
                                    Render / backups_files/
                                </td>
                            </tr>

                        </table>

                    </div>

                    <div style="
                        background:#eff6ff;
                        border:1px solid #93c5fd;
                        color:#1e3a8a;
                        border-radius:16px;
                        padding:20px 22px;
                        margin-top:26px;
                    ">

                        <div style="
                            font-size:15px;
                            font-weight:900;
                            margin-bottom:10px;
                        ">
                            Messaggio tecnico
                        </div>

                        <div style="
                            font-size:14px;
                            line-height:1.7;
                        ">
                            Backup completato correttamente.<br>
                            Il file SQL/JSON del database è stato creato e archiviato
                            su <strong>{storage_provider}</strong>.<br>
                            È stata inoltre generata la copia dei riferimenti dei documenti
                            presenti nello storage.<br>
                            Operazione conclusa senza errori.
                        </div>

                    </div>

                    <div style="
                        margin-top:30px;
                        padding-top:18px;
                        border-top:1px solid #e5e7eb;
                        color:#6b7280;
                        font-size:12px;
                        line-height:1.5;
                    ">
                        Questa email è stata generata automaticamente dal sistema di backup
                        di <strong>Studio Tecnico Cloud</strong>.
                    </div>

                </div>

            </div>

        </div>
        """

        resend.Emails.send({
            "from": settings.EMAIL_FROM_NOTIFICHE,
            "to": [settings.ALERT_EMAIL],
            "subject": "Backup completato correttamente - Studio Tecnico Cloud",
            "html": contenuto_html,
            "text": (
                "Sistema Backup - Studio Tecnico Cloud\n"
                "Backup completato correttamente.\n"
                f"Data e ora: {data_esecuzione}\n"
                f"Database: {filename_db}\n"
                f"Backup riferimenti documenti: {filename_documenti}\n"
                f"Documenti censiti: {totale_documenti}\n"
                f"Archivio definitivo: {storage_provider}\n"
                f"Percorso database: {percorso_database}\n"
                f"Percorso riferimenti documenti: {percorso_documenti}\n"
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