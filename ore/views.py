from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.shortcuts import render, redirect, get_object_or_404

from pratiche.models import Pratica
from studi.utils import get_studio_utente

from .forms import VoceOraForm
from .models import VoceOra


def accesso_negato(request):
    return render(
        request,
        'errors/accesso_negato.html',
        status=403
    )


def get_pratica_studio(request, pratica_id):

    studio = get_studio_utente(request)

    if not studio:
        return None, None

    pratica = get_object_or_404(
        Pratica,
        id=pratica_id,
        studio=studio
    )

    return studio, pratica


@login_required
def lista_ore_pratica(request, pratica_id):

    studio, pratica = get_pratica_studio(request, pratica_id)

    if not studio:
        return redirect('login')

    voci = VoceOra.objects.filter(
        pratica=pratica
    ).select_related(
        'utente',
        'pratica'
    )

    totale_ore = voci.aggregate(
        totale=Sum('ore')
    )['totale'] or Decimal('0.00')

    valore_expr = ExpressionWrapper(
        F('ore') * F('tariffa_oraria'),
        output_field=DecimalField(max_digits=12, decimal_places=2)
    )

    totale_importo = voci.filter(
        fatturabile=True
    ).aggregate(
        totale=Sum(valore_expr)
    )['totale'] or Decimal('0.00')

    totale_non_fatturato = voci.filter(
        fatturabile=True,
        inserita_in_parcella=False
    ).aggregate(
        totale=Sum(valore_expr)
    )['totale'] or Decimal('0.00')

    return render(
        request,
        'ore/lista_ore_pratica.html',
        {
            'pratica': pratica,
            'voci': voci,
            'totale_ore': totale_ore,
            'totale_importo': totale_importo,
            'totale_non_fatturato': totale_non_fatturato,
        }
    )


@login_required
def nuova_voce_ora(request, pratica_id):

    studio, pratica = get_pratica_studio(request, pratica_id)

    if not studio:
        return redirect('login')

    if request.method == 'POST':

        form = VoceOraForm(request.POST)

        if form.is_valid():

            voce = form.save(commit=False)
            voce.pratica = pratica
            voce.utente = request.user
            voce.save()

            return redirect(
                'lista_ore_pratica',
                pratica_id=pratica.id
            )

    else:

        form = VoceOraForm()

    return render(
        request,
        'ore/voce_ora_form.html',
        {
            'form': form,
            'pratica': pratica,
            'titolo': 'Nuova voce ore',
        }
    )


@login_required
def modifica_voce_ora(request, voce_id):

    studio = get_studio_utente(request)

    if not studio:
        return redirect('login')

    voce = get_object_or_404(
        VoceOra,
        id=voce_id,
        pratica__studio=studio
    )

    pratica = voce.pratica

    if request.method == 'POST':

        form = VoceOraForm(
            request.POST,
            instance=voce
        )

        if form.is_valid():

            form.save()

            return redirect(
                'lista_ore_pratica',
                pratica_id=pratica.id
            )

    else:

        form = VoceOraForm(instance=voce)

    return render(
        request,
        'ore/voce_ora_form.html',
        {
            'form': form,
            'pratica': pratica,
            'titolo': 'Modifica voce ore',
        }
    )


@login_required
def elimina_voce_ora(request, voce_id):

    studio = get_studio_utente(request)

    if not studio:
        return redirect('login')

    voce = get_object_or_404(
        VoceOra,
        id=voce_id,
        pratica__studio=studio
    )

    pratica = voce.pratica

    if request.method == 'POST':

        voce.delete()

        return redirect(
            'lista_ore_pratica',
            pratica_id=pratica.id
        )

    return render(
        request,
        'ore/elimina_voce_ora.html',
        {
            'voce': voce,
            'pratica': pratica,
        }
    )