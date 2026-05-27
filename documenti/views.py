import requests

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

from studi.utils import (
    get_studio_utente,
    studio_puo_caricare_file,
)

from attivita.models import Attivita
from pratiche.models import Pratica

from .models import Documento
from .forms import DocumentoForm, DocumentoMultiploForm


@login_required
def lista_documenti(request):

    studio = get_studio_utente(request)

    documenti = Documento.objects.filter(
        pratica__studio=studio
    ).order_by('-id')

    ricerca = request.GET.get('ricerca')

    if ricerca:

        documenti = documenti.filter(
            Q(titolo__icontains=ricerca) |
            Q(tipo_documento__icontains=ricerca) |
            Q(pratica__oggetto__icontains=ricerca) |
            Q(pratica__cliente__nome__icontains=ricerca)
        )

    context = {
        'documenti': documenti,
        'ricerca': ricerca,
    }

    return render(
        request,
        'documenti/lista_documenti.html',
        context
    )


@login_required
def carica_documento(request, pratica_id):

    studio = get_studio_utente(request)

    pratica = get_object_or_404(
        Pratica,
        id=pratica_id,
        studio=studio
    )

    if request.method == 'POST':

        form = DocumentoForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            file = request.FILES.get('file')

            if file:

                if not studio_puo_caricare_file(
                    studio,
                    file.size
                ):

                    return render(
                        request,
                        'studi/upgrade_required.html',
                        {
                            'studio': studio,
                            'titolo': 'Limite storage raggiunto',
                            'messaggio': (
                                f'Il piano FREE consente massimo '
                                f'{studio.limite_storage_mb} MB di spazio.'
                            ),
                            'azione': 'Passa al piano PRO',
                        }
                    )
            
            documento = form.save(commit=False)

            documento.pratica = pratica

            documento.save()

            Attivita.objects.create(
                pratica=pratica,
                utente=request.user,
                tipo='UPLOAD',
                descrizione=f'Caricato documento: {documento.titolo}'
            )

            return redirect(
                'dettaglio_pratica',
                pratica_id=pratica.id
            )

    else:

        form = DocumentoForm()

    context = {
        'form': form,
        'pratica': pratica,
    }

    return render(
        request,
        'documenti/carica_documento.html',
        context
    )


@login_required
def carica_documenti_multipli(request, pratica_id):

    studio = get_studio_utente(request)

    pratica = get_object_or_404(
        Pratica,
        id=pratica_id,
        studio=studio
    )

    if request.method == 'POST':

        form = DocumentoMultiploForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            files = request.FILES.getlist('files')

            dimensione_totale = 0

            for file in files:
                dimensione_totale += file.size

            if not studio_puo_caricare_file(
                studio,
                dimensione_totale
            ):

                return render(
                    request,
                    'studi/upgrade_required.html',
                    {
                        'studio': studio,
                        'titolo': 'Limite storage raggiunto',
                        'messaggio': (
                            f'Il piano FREE consente massimo '
                            f'{studio.limite_storage_mb} MB di spazio.'
                        ),
                        'azione': 'Passa al piano PRO',
                    }
                ) 

            for file in files:

                print("FILE:", file.name)

                nome_file = file.name.lower()

                if (
                    nome_file.endswith('.zip') or
                    nome_file.endswith('.rar') or
                    nome_file.endswith('.7z')
                ):

                    form.add_error(
                        'files',
                        'I file ZIP/RAR/7Z non sono supportati dal caricamento cloud.'
                    )

                    return render(
                        request,
                        'documenti/carica_documenti_multipli.html',
                        {
                            'form': form,
                            'pratica': pratica,
                        }
                    )

            titolo_base = form.cleaned_data.get('titolo_base')
            tipo_documento = form.cleaned_data.get('tipo_documento')
            note = form.cleaned_data.get('note')

            for file in files:

                titolo = titolo_base if titolo_base else file.name

                documento = Documento.objects.create(
                    pratica=pratica,
                    titolo=titolo,
                    tipo_documento=tipo_documento,
                    file=file,
                    note=note
                )

                Attivita.objects.create(
                    pratica=pratica,
                    utente=request.user,
                    tipo='UPLOAD',
                    descrizione=f'Caricato documento: {documento.titolo}'
                )

            return redirect(
                'dettaglio_pratica',
                pratica_id=pratica.id
            )

        print(form.errors)

    else:

        form = DocumentoMultiploForm()

    return render(
        request,
        'documenti/carica_documenti_multipli.html',
        {
            'form': form,
            'pratica': pratica,
        }
    )

@login_required
def elimina_documento(request, documento_id):

    studio = get_studio_utente(request)

    documento = get_object_or_404(
        Documento,
        id=documento_id,
        pratica__studio=studio
    )

    pratica = documento.pratica

    pratica_id = pratica.id

    titolo_documento = documento.titolo

    if request.method == 'POST':

        documento.file.delete(save=False)

        documento.delete()

        Attivita.objects.create(
            pratica=pratica,
            utente=request.user,
            tipo='ELIMINAZIONE',
            descrizione=f'Eliminato documento: {titolo_documento}'
        )

        return redirect(
            'dettaglio_pratica',
            pratica_id=pratica_id
        )

    return render(
        request,
        'documenti/elimina_documento.html',
        {
            'documento': documento
        }
    )


@login_required
def verifica_documenti_cloud(request):

    studio = get_studio_utente(request)

    risultati = []

    documenti = Documento.objects.filter(
        pratica__studio=studio
    ).order_by('id')

    for documento in documenti:

        stato = 'OK'

        file_url = ''

        try:

            file_url = documento.file.url

            response = requests.get(
                file_url,
                timeout=10,
                stream=True
            )

            if response.status_code not in [200, 301, 302]:

                stato = (
                    f'FILE NON RAGGIUNGIBILE '
                    f'({response.status_code})'
                )

        except Exception:

            stato = 'ERRORE FILE'

        risultati.append({
            'id': documento.id,
            'titolo': documento.titolo,
            'pratica': documento.pratica,
            'url': file_url,
            'stato': stato,
        })

    context = {
        'risultati': risultati
    }

    return render(
        request,
        'documenti/verifica_cloud.html',
        context
    )