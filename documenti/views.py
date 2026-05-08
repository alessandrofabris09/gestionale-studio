from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

from pratiche.models import Pratica
from .models import Documento
from .forms import DocumentoForm, DocumentoMultiploForm


@login_required
def lista_documenti(request):

    documenti = Documento.objects.all().order_by('-id')

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

    pratica = get_object_or_404(
        Pratica,
        id=pratica_id
    )

    if request.method == 'POST':

        form = DocumentoForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            documento = form.save(commit=False)
            documento.pratica = pratica
            documento.save()

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

    pratica = get_object_or_404(
        Pratica,
        id=pratica_id
    )

    if request.method == 'POST':

        form = DocumentoMultiploForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            files = request.FILES.getlist('files')

            titolo_base = form.cleaned_data.get('titolo_base')

            tipo_documento = form.cleaned_data.get('tipo_documento')

            note = form.cleaned_data.get('note')

            for file in files:

                titolo = titolo_base if titolo_base else file.name

                Documento.objects.create(
                    pratica=pratica,
                    titolo=titolo,
                    tipo_documento=tipo_documento,
                    file=file,
                    note=note
                )

            return redirect(
                'dettaglio_pratica',
                pratica_id=pratica.id
            )

    else:

        form = DocumentoMultiploForm()

    context = {
        'form': form,
        'pratica': pratica,
    }

    return render(
        request,
        'documenti/carica_documenti_multipli.html',
        context
    )


@login_required
def elimina_documento(request, documento_id):

    documento = get_object_or_404(
        Documento,
        id=documento_id
    )

    pratica_id = documento.pratica.id

    if request.method == 'POST':

        documento.file.delete(save=False)

        documento.delete()

        return redirect(
            'dettaglio_pratica',
            pratica_id=pratica_id
        )

    return render(
        request,
        'documenti/elimina_documento.html',
        {'documento': documento}
    )