from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

from .models import Immobile
from .forms import ImmobileForm


@login_required
def lista_immobili(request):

    immobili = Immobile.objects.all().order_by('comune', 'indirizzo')

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

    return render(request, 'immobili/lista_immobili.html', context)


@login_required
def nuovo_immobile(request):

    if request.method == 'POST':
        form = ImmobileForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('lista_immobili')
    else:
        form = ImmobileForm()

    return render(request, 'immobili/nuovo_immobile.html', {'form': form})


@login_required
def dettaglio_immobile(request, immobile_id):

    immobile = get_object_or_404(Immobile, id=immobile_id)
    pratiche = immobile.pratica_set.all()

    context = {
        'immobile': immobile,
        'pratiche': pratiche,
    }

    return render(request, 'immobili/dettaglio_immobile.html', context)


@login_required
def modifica_immobile(request, immobile_id):

    immobile = get_object_or_404(Immobile, id=immobile_id)

    if request.method == 'POST':
        form = ImmobileForm(request.POST, instance=immobile)

        if form.is_valid():
            form.save()
            return redirect('dettaglio_immobile', immobile_id=immobile.id)
    else:
        form = ImmobileForm(instance=immobile)

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

    immobile = get_object_or_404(Immobile, id=immobile_id)

    if request.method == 'POST':
        immobile.delete()
        return redirect('lista_immobili')

    return render(
        request,
        'immobili/elimina_immobile.html',
        {'immobile': immobile}
    )