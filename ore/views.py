from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from pratiche.models import Pratica
from studi.utils import get_studio_utente
from studi.permessi import (
    puo_modificare_parcelle,
)

from attivita.models import Attivita
from parcelle.models import Parcella

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


def valore_ore_expr():
    return ExpressionWrapper(
        F('ore') * F('tariffa_oraria'),
        output_field=DecimalField(
            max_digits=12,
            decimal_places=2
        )
    )


@login_required
def lista_ore_pratica(request, pratica_id):

    studio, pratica = get_pratica_studio(
        request,
        pratica_id
    )

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

    valore_expr = valore_ore_expr()

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

    ore_non_fatturate = voci.filter(
        fatturabile=True,
        inserita_in_parcella=False
    ).aggregate(
        totale=Sum('ore')
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
            'ore_non_fatturate': ore_non_fatturate,
        }
    )


@login_required
def nuova_voce_ora(request, pratica_id):

    studio, pratica = get_pratica_studio(
        request,
        pratica_id
    )

    if not studio:
        return redirect('login')

    if request.method == 'POST':

        form = VoceOraForm(request.POST)

        if form.is_valid():

            voce = form.save(commit=False)
            voce.pratica = pratica
            voce.utente = request.user
            voce.save()

            Attivita.objects.create(
                pratica=pratica,
                utente=request.user,
                tipo='ALTRO',
                descrizione=(
                    f'Inserita voce ore: '
                    f'{voce.get_tipo_attivita_display()} - '
                    f'{voce.ore} ore'
                )
            )

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

            Attivita.objects.create(
                pratica=pratica,
                utente=request.user,
                tipo='MODIFICA',
                descrizione='Modificata voce ore lavorate'
            )

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

        Attivita.objects.create(
            pratica=pratica,
            utente=request.user,
            tipo='ELIMINAZIONE',
            descrizione='Eliminata voce ore lavorate'
        )

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


@login_required
def genera_parcella_da_ore(request, pratica_id):

    if not puo_modificare_parcelle(request):
        return accesso_negato(request)

    studio, pratica = get_pratica_studio(
        request,
        pratica_id
    )

    if not studio:
        return redirect('login')

    voci_da_fatturare = VoceOra.objects.filter(
        pratica=pratica,
        fatturabile=True,
        inserita_in_parcella=False
    )

    valore_expr = valore_ore_expr()

    totale_importo = voci_da_fatturare.aggregate(
        totale=Sum(valore_expr)
    )['totale'] or Decimal('0.00')

    totale_ore = voci_da_fatturare.aggregate(
        totale=Sum('ore')
    )['totale'] or Decimal('0.00')

    if totale_importo <= 0:

        return render(
            request,
            'ore/nessuna_ora_da_fatturare.html',
            {
                'pratica': pratica,
            }
        )

    if request.method == 'POST':

        descrizione = (
            f'Compenso professionale per attività svolte sulla pratica '
            f'"{pratica.oggetto}", come da consuntivo ore lavorate. '
            f'Totale ore fatturabili: {totale_ore}.'
        )

        parcella = Parcella.objects.create(
            pratica=pratica,
            tipo_documento='PARCELLA',
            descrizione=descrizione,
            importo=totale_importo,
            data_emissione=timezone.now().date(),
        )

        voci_da_fatturare.update(
            inserita_in_parcella=True
        )

        Attivita.objects.create(
            pratica=pratica,
            utente=request.user,
            tipo='PARCELLA',
            descrizione=(
                f'Generata parcella da consuntivo ore: '
                f'{parcella.numero_documento}'
            )
        )

        return redirect(
            'modifica_parcella',
            parcella_id=parcella.id
        )

    return render(
        request,
        'ore/conferma_genera_parcella.html',
        {
            'pratica': pratica,
            'totale_importo': totale_importo,
            'totale_ore': totale_ore,
            'voci_da_fatturare': voci_da_fatturare,
        }
    )