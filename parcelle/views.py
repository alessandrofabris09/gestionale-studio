from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

from .models import Parcella
from .forms import ParcellaForm


@login_required
def lista_parcelle(request):
    parcelle = Parcella.objects.all().order_by('-id')

    ricerca = request.GET.get('ricerca')

    if ricerca:
        parcelle = parcelle.filter(
            Q(descrizione__icontains=ricerca) |
            Q(pratica__oggetto__icontains=ricerca) |
            Q(pratica__cliente__nome__icontains=ricerca)
        )

    return render(
        request,
        'parcelle/lista_parcelle.html',
        {
            'parcelle': parcelle,
            'ricerca': ricerca,
        }
    )


@login_required
def nuova_parcella(request):
    if request.method == 'POST':
        form = ParcellaForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('lista_parcelle')
    else:
        form = ParcellaForm()

    return render(
        request,
        'parcelle/nuova_parcella.html',
        {'form': form}
    )


@login_required
def modifica_parcella(request, parcella_id):
    parcella = get_object_or_404(Parcella, id=parcella_id)

    if request.method == 'POST':
        form = ParcellaForm(request.POST, instance=parcella)

        if form.is_valid():
            form.save()
            return redirect('lista_parcelle')
    else:
        form = ParcellaForm(instance=parcella)

    return render(
        request,
        'parcelle/modifica_parcella.html',
        {
            'form': form,
            'parcella': parcella,
        }
    )


@login_required
def elimina_parcella(request, parcella_id):
    parcella = get_object_or_404(Parcella, id=parcella_id)

    if request.method == 'POST':
        parcella.delete()
        return redirect('lista_parcelle')

    return render(
        request,
        'parcelle/elimina_parcella.html',
        {'parcella': parcella}
    )