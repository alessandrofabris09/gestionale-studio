from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

from .models import Cliente
from .forms import ClienteForm

from studi.utils import get_studio_utente
from studi.permessi import (
    is_titolare,
    is_tecnico,
    is_segreteria,
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


def puo_accedere_clienti(request):
    """
    Accesso all'area clienti consentito a:
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


def puo_modificare_clienti(request):
    """
    Creazione/modifica clienti consentita a:
    - superuser
    - TITOLARE
    - TECNICO
    - SEGRETERIA
    """

    return puo_accedere_clienti(request)


def puo_eliminare_clienti(request):
    """
    Eliminazione clienti consentita solo a:
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
def lista_clienti(request):

    if not puo_accedere_clienti(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if request.user.is_superuser:
        clienti = Cliente.objects.all().order_by('nome')
    else:
        clienti = Cliente.objects.filter(
            studio=studio
        ).order_by('nome')

    ricerca = request.GET.get('ricerca')

    if ricerca:

        clienti = clienti.filter(
            Q(nome__icontains=ricerca) |
            Q(email__icontains=ricerca) |
            Q(telefono__icontains=ricerca) |
            Q(codice_fiscale__icontains=ricerca) |
            Q(partita_iva__icontains=ricerca)
        )

    context = {
        'clienti': clienti,
        'ricerca': ricerca,
    }

    return render(
        request,
        'clienti/lista_clienti.html',
        context
    )


@login_required
def nuovo_cliente(request):

    if not puo_modificare_clienti(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    if request.method == 'POST':

        form = ClienteForm(request.POST)

        if form.is_valid():

            cliente = form.save(commit=False)
            cliente.studio = studio
            cliente.save()

            return redirect('lista_clienti')

    else:

        form = ClienteForm()

    return render(
        request,
        'clienti/nuovo_cliente.html',
        {
            'form': form
        }
    )


@login_required
def dettaglio_cliente(request, cliente_id):

    if not puo_accedere_clienti(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if request.user.is_superuser:
        cliente = get_object_or_404(
            Cliente,
            id=cliente_id
        )

        pratiche = cliente.pratica_set.all()

    else:
        cliente = get_object_or_404(
            Cliente,
            id=cliente_id,
            studio=studio
        )

        pratiche = cliente.pratica_set.filter(
            studio=studio
        )

    context = {
        'cliente': cliente,
        'pratiche': pratiche,
    }

    return render(
        request,
        'clienti/dettaglio_cliente.html',
        context
    )


@login_required
def modifica_cliente(request, cliente_id):

    if not puo_modificare_clienti(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if request.user.is_superuser:
        cliente = get_object_or_404(
            Cliente,
            id=cliente_id
        )
    else:
        cliente = get_object_or_404(
            Cliente,
            id=cliente_id,
            studio=studio
        )

    if request.method == 'POST':

        form = ClienteForm(
            request.POST,
            instance=cliente
        )

        if form.is_valid():

            cliente = form.save()

            return redirect(
                'dettaglio_cliente',
                cliente_id=cliente.id
            )

    else:

        form = ClienteForm(instance=cliente)

    return render(
        request,
        'clienti/modifica_cliente.html',
        {
            'form': form,
            'cliente': cliente,
        }
    )


@login_required
def elimina_cliente(request, cliente_id):

    if not puo_eliminare_clienti(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if request.user.is_superuser:
        cliente = get_object_or_404(
            Cliente,
            id=cliente_id
        )
    else:
        cliente = get_object_or_404(
            Cliente,
            id=cliente_id,
            studio=studio
        )

    if request.method == 'POST':

        cliente.delete()

        return redirect('lista_clienti')

    return render(
        request,
        'clienti/elimina_cliente.html',
        {
            'cliente': cliente
        }
    )