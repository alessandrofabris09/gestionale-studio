from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

from .models import Cliente
from .forms import ClienteForm

from studi.utils import get_studio_utente


@login_required
def lista_clienti(request):

    studio = get_studio_utente(request)

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

    studio = get_studio_utente(request)

    if not studio:
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

    studio = get_studio_utente(request)

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

    studio = get_studio_utente(request)

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

            cliente = form.save(commit=False)
            cliente.studio = studio
            cliente.save()

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

    studio = get_studio_utente(request)

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
        {'cliente': cliente}
    )