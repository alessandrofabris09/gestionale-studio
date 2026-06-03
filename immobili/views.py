from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

from studi.utils import get_studio_utente
from studi.permessi import (
    is_titolare,
    is_tecnico,
    is_segreteria,
)

from .models import Immobile
from .forms import ImmobileForm


def accesso_negato(request):
    """
    Pagina grafica di blocco accesso.
    """

    return render(
        request,
        'errors/accesso_negato.html',
        status=403
    )

def puo_accedere_immobili(request):
    """
    Accesso all'area immobili consentito a:
    - superuser
    - TITOLARE
    - TECNICO
    - SEGRETERIA

    Non consentito a:
    - COLLABORATORE
    """

    if not request.user.is_authenticated:
        return False

    return (
        request.user.is_superuser or
        is_titolare(request) or
        is_tecnico(request) or
        is_segreteria(request)
    )


def puo_modificare_immobili(request):
    """
    Creazione/modifica immobili consentita a:
    - superuser
    - TITOLARE
    - TECNICO
    - SEGRETERIA
    """

    return puo_accedere_immobili(request)


def puo_eliminare_immobili(request):
    """
    Eliminazione immobili consentita solo a:
    - superuser
    - TITOLARE
    """

    if not request.user.is_authenticated:
        return False

    return (
        request.user.is_superuser or
        is_titolare(request)
    )


@login_required
def lista_immobili(request):

    if not puo_accedere_immobili(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    if request.user.is_superuser:
        immobili = Immobile.objects.all().order_by('comune', 'indirizzo')
    else:
        immobili = Immobile.objects.filter(
            studio=studio
        ).order_by('comune', 'indirizzo')

    ricerca = request.GET.get('ricerca')

    if ricerca:
        immobili = immobili.filter(
            Q(comune__icontains=ricerca) |
            Q(indirizzo__icontains=ricerca) |
            Q(foglio__icontains=ricerca) |
            Q(mappale__icontains=ricerca) |
            Q(subalterno__icontains=ricerca) |
            Q(cliente__nome__icontains=ricerca)
        )

    context = {
        'immobili': immobili,
        'ricerca': ricerca,
    }

    return render(
        request,
        'immobili/lista_immobili.html',
        context
    )


@login_required
def nuovo_immobile(request):

    if not puo_modificare_immobili(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    if request.method == 'POST':

        form = ImmobileForm(
            request.POST,
            studio=studio
        )

        if form.is_valid():

            immobile = form.save(commit=False)
            immobile.studio = studio
            immobile.save()

            return redirect('lista_immobili')

    else:

        form = ImmobileForm(
            studio=studio
        )

    return render(
        request,
        'immobili/nuovo_immobile.html',
        {
            'form': form
        }
    )


@login_required
def dettaglio_immobile(request, immobile_id):

    if not puo_accedere_immobili(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if request.user.is_superuser:
        immobile = get_object_or_404(
            Immobile,
            id=immobile_id
        )

        pratiche = immobile.pratica_set.all()

    else:
        immobile = get_object_or_404(
            Immobile,
            id=immobile_id,
            studio=studio
        )

        pratiche = immobile.pratica_set.filter(
            studio=studio
        )

    context = {
        'immobile': immobile,
        'pratiche': pratiche,
    }

    return render(
        request,
        'immobili/dettaglio_immobile.html',
        context
    )


@login_required
def modifica_immobile(request, immobile_id):

    if not puo_modificare_immobili(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if request.user.is_superuser:
        immobile = get_object_or_404(
            Immobile,
            id=immobile_id
        )
    else:
        immobile = get_object_or_404(
            Immobile,
            id=immobile_id,
            studio=studio
        )

    if request.method == 'POST':

        form = ImmobileForm(
            request.POST,
            instance=immobile,
            studio=studio
        )

        if form.is_valid():

            immobile = form.save(commit=False)
            immobile.studio = studio
            immobile.save()

            return redirect(
                'dettaglio_immobile',
                immobile_id=immobile.id
            )

    else:

        form = ImmobileForm(
            instance=immobile,
            studio=studio
        )

    return render(
        request,
        'immobili/modifica_immobile.html',
        {
            'form': form,
            'immobile': immobile,
        }
    )


@login_required
def elimina_immobile(request, immobile_id):

    if not puo_eliminare_immobili(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if request.user.is_superuser:
        immobile = get_object_or_404(
            Immobile,
            id=immobile_id
        )
    else:
        immobile = get_object_or_404(
            Immobile,
            id=immobile_id,
            studio=studio
        )

    if request.method == 'POST':

        immobile.delete()

        return redirect('lista_immobili')

    return render(
        request,
        'immobili/elimina_immobile.html',
        {
            'immobile': immobile
        }
    )