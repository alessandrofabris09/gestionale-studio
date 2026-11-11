"""Prova temporanea di deploy sul servizio Render di collaudo."""
import json
import os
from datetime import timedelta
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management import call_command
from django.db import transaction
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from clienti.models import Cliente
from documenti.models import Documento
from immobili.models import Immobile
from pratiche.models import Pratica
from studi.beta_pro import attiva_beta_pro
from studi.models import ProfiloUtente, Studio

HOST = 'studio-tecnico-collaudo.onrender.com'
if (
    os.environ.get('RENDER_EXTERNAL_HOSTNAME') != HOST
    or os.environ.get('RENDER_GIT_BRANCH') != 'collaudo-render'
    or settings.SETTINGS_MODULE != 'gestionale.settings_staging'
    or settings.ALLOWED_HOSTS != [HOST]
):
    raise RuntimeError('BETA_QA: esecuzione ammessa esclusivamente sul collaudo Render.')
if not settings.USE_BACKBLAZE_B2 or not any(
    parola in default_storage.bucket_name.lower() for parola in ('collaud', 'staging', 'test')
):
    raise RuntimeError('BETA_QA: serve il bucket B2 dedicato al collaudo.')
if settings.EMAIL_BACKEND != 'anymail.backends.resend.EmailBackend':
    raise RuntimeError('BETA_QA: il backend email di collaudo deve essere Resend.')


def richiedi(condizione, messaggio):
    if not condizione:
        raise RuntimeError('BETA_QA: ' + messaggio)


def crea_studio(suffisso, email=''):
    user = User.objects.create(username=f'qa-beta-{suffisso}', email=email)
    studio = Studio.objects.create(nome='Studio fittizio QA Beta', titolare=user)
    ProfiloUtente.objects.create(user=user, studio=studio, ruolo='TITOLARE')
    cliente = Cliente.objects.create(studio=studio, nome='Cliente fittizio QA')
    immobile = Immobile.objects.create(studio=studio, cliente=cliente, comune='Comune fittizio QA')
    pratica = Pratica.objects.create(studio=studio, cliente=cliente, immobile=immobile, oggetto='Pratica fittizia QA')
    return user, studio, pratica


with transaction.atomic():
    marker = uuid4().hex
    utente, studio, pratica = crea_studio(marker, 'delivered@resend.dev')
    _, _, pratica_esterna = crea_studio(marker + '-secondo')
    beta, nuova = attiva_beta_pro(studio.pk)
    richiedi(nuova, 'ammissione non creata')
    client = Client(HTTP_HOST=HOST)
    client.force_login(utente)
    percorso_abbonamento = reverse('abbonamento')
    abbonamento = client.get(percorso_abbonamento, secure=True)
    richiedi(abbonamento.status_code == 200 and b'500 MB' in abbonamento.content, 'beta attiva non visibile')
    print('BETA_QA PASS attivazione e quota', flush=True)

    oggi = timezone.localdate()
    beta.fine_pro_il = oggi + timedelta(days=30)
    beta.fine_esportazione_il = oggi + timedelta(days=60)
    beta.save(update_fields=['fine_pro_il', 'fine_esportazione_il'])
    call_command('avvisa_scadenza_beta', studio_id=studio.pk)
    beta.refresh_from_db()
    richiedi(beta.avvisata_il is not None, 'avviso non accettato')
    call_command('avvisa_scadenza_beta', studio_id=studio.pk)
    print('BETA_QA PASS avviso Resend accettato e secondo invio evitato', flush=True)

    documento = Documento(pratica=pratica, titolo='Allegato fittizio QA Beta')
    contenuto = b'Documento fittizio di collaudo Studio Tecnico Cloud\n'
    documento.file.save(f'qa-beta-{marker}.txt', ContentFile(contenuto), save=False)
    try:
        documento.save()
        richiedi(default_storage.exists(documento.file.name), 'allegato non trovato in B2')
        beta.attivata_il = oggi - timedelta(days=190)
        beta.fine_pro_il = oggi
        beta.fine_esportazione_il = oggi + timedelta(days=30)
        beta.save(update_fields=['attivata_il', 'fine_pro_il', 'fine_esportazione_il'])
        lettura = client.get(reverse('dettaglio_pratica', args=[pratica.pk]), secure=True)
        scrittura = client.post(reverse('elimina_pratica', args=[pratica.pk]), secure=True)
        richiedi(lettura.status_code == 200 and scrittura.status_code == 403, 'sola lettura non rispettata')
        risposta = client.post(reverse('esporta_beta'), secure=True)
        richiedi(risposta.status_code == 200, f'esportazione HTTP {risposta.status_code}')
        with ZipFile(BytesIO(b''.join(risposta.streaming_content))) as archivio:
            richiedi(archivio.read(f'allegati/{documento.pk}') == contenuto, 'contenuto B2 diverso')
            dati = json.loads(archivio.read('dati-operativi.json'))
            pratiche = {r['pk'] for r in dati if r['model'] == 'pratiche.pratica'}
            richiedi(pratiche == {pratica.pk} and pratica_esterna.pk not in pratiche, 'isolamento ZIP non rispettato')
        beta.fine_pro_il = oggi - timedelta(days=30)
        beta.fine_esportazione_il = oggi
        beta.save(update_fields=['fine_pro_il', 'fine_esportazione_il'])
        chiusa = client.post(reverse('esporta_beta'), secure=True)
        richiedi(chiusa.status_code == 403, 'download ancora attivo dopo chiusura')
        print('BETA_QA PASS sola lettura, ZIP Backblaze, isolamento e chiusura', flush=True)
    finally:
        default_storage.delete(documento.file.name)
        richiedi(not default_storage.exists(documento.file.name), 'allegato fittizio non rimosso')
    transaction.set_rollback(True)

richiedi(not User.objects.filter(username__startswith=f'qa-beta-{marker}').exists(), 'account fittizi rimasti')
print('BETA_QA PASS dati fittizi rimossi', flush=True)
