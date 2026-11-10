from django.views.decorators.http import require_POST
from studi.permessi import puo_gestire_abbonamento
import os
from uuid import uuid4
import stripe

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils.timezone import now
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from studi.utils import get_studio_utente
from studi.models import Studio


stripe.api_key = settings.STRIPE_SECRET_KEY


def attiva_piano_pro(studio, customer_id=None, subscription_id=None):
    """
    Attiva il piano PRO per lo studio.
    Deve essere richiamata solo dopo conferma Stripe valida.
    """

    studio.piano = 'PRO'
    studio.stato_abbonamento = 'ATTIVO'

    if customer_id:
        studio.stripe_customer_id = customer_id

    if subscription_id:
        studio.stripe_subscription_id = subscription_id

    studio.limite_pratiche = 999999
    studio.limite_utenti = 999999
    studio.limite_storage_mb = 50000

    studio.save()


def disattiva_piano_pro(studio):
    """
    Riporta lo studio al piano FREE quando l'abbonamento Stripe
    viene cancellato, sospeso o risulta non pagato.
    """

    studio.piano = 'FREE'
    studio.stato_abbonamento = 'SCADUTO'

    studio.stripe_subscription_id = ''
    studio.stripe_checkout_pending = {}

    studio.limite_pratiche = 20
    studio.limite_utenti = 1
    studio.limite_storage_mb = 500

    studio.save()


def aggiorna_stato_abbonamento(studio, stato):
    """
    Aggiorna solo lo stato dell'abbonamento senza cambiare piano e limiti.
    """

    studio.stato_abbonamento = stato
    studio.save()


def abbonamento_da_fattura(invoice):
    parent = invoice.get('parent') or {}
    details = parent.get('subscription_details') or {}
    subscription = details.get('subscription') or invoice.get('subscription')
    if isinstance(subscription, dict):
        return subscription.get('id')
    return subscription


def allinea_abbonamento_stripe(subscription_id, *, cancellato=False):
    if not subscription_id:
        return

    with transaction.atomic():
        studio = Studio.objects.select_for_update().filter(
            stripe_subscription_id=subscription_id
        ).first()
        if studio is None:
            return

        if cancellato:
            disattiva_piano_pro(studio)
            return

        # Gli eventi possono arrivare duplicati o fuori ordine. Leggere Stripe
        # dopo aver bloccato la riga impedisce di applicare uno stato arretrato.
        subscription = stripe.Subscription.retrieve(subscription_id)
        if subscription.status in ('active', 'trialing'):
            attiva_piano_pro(studio, subscription.customer, subscription_id)
        elif subscription.status == 'canceled':
            disattiva_piano_pro(studio)
        elif subscription.status in (
            'past_due', 'unpaid', 'incomplete', 'incomplete_expired', 'paused',
        ):
            aggiorna_stato_abbonamento(studio, 'SCADUTO')


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Webhook Stripe.

    Il piano PRO viene attivato solo da eventi Stripe verificati.
    La pagina success non attiva mai il piano PRO.
    """

    payload = request.body

    sig_header = request.META.get(
        'HTTP_STRIPE_SIGNATURE'
    )

    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    if not endpoint_secret or not sig_header:
        return HttpResponse(status=400)

    try:

        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            endpoint_secret
        ).to_dict()

    except ValueError:

        return HttpResponse(
            status=400
        )

    except stripe.error.SignatureVerificationError:

        return HttpResponse(
            status=400
        )

    event_type = event.get(
        'type'
    )

    # =========================
    # CHECKOUT COMPLETATO
    # =========================

    if event_type == 'checkout.session.completed':

        session = event['data']['object']

        metadata = session.get(
            'metadata',
            {}
        )

        studio_id = metadata.get(
            'studio_id'
        )

        mode = session.get(
            'mode'
        )

        payment_status = session.get(
            'payment_status'
        )

        subscription_id = session.get(
            'subscription'
        )

        customer_id = session.get(
            'customer'
        )

        if (
            studio_id and
            mode == 'subscription' and
            payment_status == 'paid' and
            subscription_id
        ):

            try:

                with transaction.atomic():
                    studio = Studio.objects.select_for_update().get(id=studio_id)
                    # I rinnovi aggiornano lo stato tramite gli eventi di fattura.
                    if not studio.stripe_subscription_id:
                        subscription = stripe.Subscription.retrieve(subscription_id)
                        if subscription.status not in ('active', 'trialing'):
                            return HttpResponse(status=200)
                        studio.stripe_checkout_pending = {}
                        attiva_piano_pro(
                            studio=studio,
                            customer_id=customer_id,
                            subscription_id=subscription_id,
                        )

            except Studio.DoesNotExist:

                pass

            except stripe.error.StripeError:
                return HttpResponse(status=503)

    elif event_type in (
        'invoice.paid',
        'invoice.payment_failed',
        'customer.subscription.updated',
        'customer.subscription.deleted',
    ):
        oggetto = event['data']['object']
        subscription_id = (
            abbonamento_da_fattura(oggetto)
            if event_type.startswith('invoice.')
            else oggetto.get('id')
        )
        try:
            allinea_abbonamento_stripe(
                subscription_id,
                cancellato=event_type == 'customer.subscription.deleted',
            )
        except stripe.error.StripeError:
            # Stripe ritenterà la consegna. Lo studio resta nello stato precedente.
            return HttpResponse(status=503)

    return HttpResponse(
        status=200
    )


@login_required
@require_POST
def checkout_pro(request):
    """
    Crea la sessione Stripe Checkout per passare al piano PRO.

    Usa come email principale quella dello studio.
    Se esiste già un cliente Stripe, aggiorna anche la sua email.
    """

    if not puo_gestire_abbonamento(request):
        return render(request, 'errors/accesso_negato.html', status=403)

    studio = get_studio_utente(request)

    if not studio:

        return redirect(
            'login'
        )

    if studio.is_pro() or studio.stripe_subscription_id:
        return redirect('abbonamento')

    coupon_primo_anno = os.environ.get('STRIPE_COUPON_PRO_FIRST_YEAR', '').strip()
    modalita_live = settings.STRIPE_SECRET_KEY.startswith(('sk_live_', 'rk_live_'))
    if not all((
        settings.STRIPE_SECRET_KEY,
        settings.STRIPE_PRICE_PRO_MONTHLY,
        settings.STRIPE_WEBHOOK_SECRET,
    )) or (modalita_live and not coupon_primo_anno):

        return render(
            request,
            'billing/success.html',
            {
                'studio': studio,
                'errore': (
                    'Stripe non è ancora configurato correttamente. '
                    'Contatta il supporto.'
                )
            }
        )

    email_checkout = studio.email or request.user.email

    checkout_data = {
        'mode': 'subscription',

        'line_items': [
            {
                'price': settings.STRIPE_PRICE_PRO_MONTHLY,
                'quantity': 1,
            }
        ],

        'success_url': (
            settings.SITE_URL +
            '/billing/success/?session_id={CHECKOUT_SESSION_ID}'
        ),

        'cancel_url': (
            settings.SITE_URL +
            '/studi/abbonamento/'
        ),

        'metadata': {
            'studio_id': str(studio.id),
            'user_id': str(request.user.id),
        },

        'subscription_data': {
            'metadata': {
                'studio_id': str(studio.id),
                'user_id': str(request.user.id),
            }
        },

        'billing_address_collection': 'auto',
    }

    if studio.stripe_customer_id:
        checkout_data['customer'] = studio.stripe_customer_id

    else:

        checkout_data['customer_email'] = email_checkout

    if coupon_primo_anno:

        checkout_data['discounts'] = [
            {
                'coupon': coupon_primo_anno
            }
        ]

    try:
        while True:
            with transaction.atomic():
                studio = Studio.objects.select_for_update().get(pk=studio.pk)
                if studio.is_pro() or studio.stripe_subscription_id:
                    return redirect('abbonamento')
                pending = studio.stripe_checkout_pending
                if not pending:
                    pending = {
                        'key': str(uuid4()),
                        'payload': checkout_data,
                        'created': int(now().timestamp()),
                    }
                    studio.stripe_checkout_pending = pending
                    studio.save(update_fields=['stripe_checkout_pending'])

            with transaction.atomic():
                studio = Studio.objects.select_for_update().get(pk=studio.pk)
                if studio.is_pro() or studio.stripe_subscription_id:
                    return redirect('abbonamento')
                pending = studio.stripe_checkout_pending
                if not pending:
                    continue

                if pending.get('session_id'):
                    session = stripe.checkout.Session.retrieve(pending['session_id'])
                else:
                    # Stripe può rimuovere la chiave dopo 24 ore. Se l'esito
                    # resta incerto, serve una verifica prima di ricreare.
                    if now().timestamp() - pending['created'] >= 23 * 3600:
                        return render(request, 'billing/success.html', {
                            'studio': studio,
                            'errore': 'Il checkout precedente richiede una verifica. Contatta il supporto.',
                        })
                    if pending['payload'].get('customer'):
                        try:
                            stripe.Customer.modify(
                                pending['payload']['customer'],
                                email=email_checkout,
                                name=studio.nome,
                            )
                        except stripe.error.StripeError:
                            pass
                    session = stripe.checkout.Session.create(
                        **pending['payload'], idempotency_key=pending['key'],
                    )
                    pending['session_id'] = session.id
                    studio.save(update_fields=['stripe_checkout_pending'])

                if session.status == 'expired':
                    studio.stripe_checkout_pending = {}
                    studio.save(update_fields=['stripe_checkout_pending'])
                    continue
                break
    except stripe.error.StripeError:
        return render(request, 'billing/success.html', {
            'studio': studio,
            'errore': 'Il servizio di pagamento non è disponibile. Riprova più tardi.',
        })

    if session.status != 'open' or not session.url:
        return redirect(reverse('checkout_success', query={'session_id': session.id}))

    return redirect(
        session.url,
        permanent=False
    )


@login_required
def checkout_success(request):
    """
    Pagina di ritorno dopo Stripe Checkout.

    Verifica la sessione direttamente con Stripe usando session_id.
    La pagina e informativa: non modifica mai lo stato del piano.
    """

    if not puo_gestire_abbonamento(request):
        return render(request, 'errors/accesso_negato.html', status=403)

    studio = get_studio_utente(request)

    session_id = request.GET.get(
        'session_id'
    )

    messaggio = None
    errore = None

    if not studio:

        return redirect(
            'login'
        )

    if not session_id:

        errore = (
            'Sessione Stripe non trovata. '
            'Non è stato possibile verificare automaticamente il pagamento.'
        )

        return render(
            request,
            'billing/success.html',
            {
                'studio': studio,
                'messaggio': messaggio,
                'errore': errore,
            }
        )

    try:

        session = stripe.checkout.Session.retrieve(
            session_id
        )

        metadata = getattr(
            session,
            'metadata',
            None
        )

        studio_id = None

        if metadata:

            try:
                studio_id = metadata['studio_id']

            except Exception:

                studio_id = getattr(
                    metadata,
                    'studio_id',
                    None
                )

        mode = getattr(
            session,
            'mode',
            None
        )

        payment_status = getattr(
            session,
            'payment_status',
            None
        )

        status = getattr(
            session,
            'status',
            None
        )

        subscription_id = getattr(
            session,
            'subscription',
            None
        )

        if (
            str(studio.id) == str(studio_id) and
            mode == 'subscription' and
            status == 'complete' and
            payment_status == 'paid' and
            subscription_id
        ):

            # Una vecchia sessione pagata non prova che l'abbonamento sia
            # ancora attivo: soltanto i webhook firmati aggiornano lo studio.
            messaggio = (
                'Pagamento verificato. Il piano PRO risulta attivo.'
                if studio.is_pro() else
                'Pagamento verificato. Lo stato del piano viene aggiornato '
                'dalle notifiche sicure del servizio di pagamento. '
                'Se il piano non si aggiorna, contatta il supporto.'
            )

        else:

            errore = (
                'Non è stato possibile confermare un pagamento completato per questo studio. '
                'Controlla il piano o contatta il supporto.'
            )

    except stripe.error.StripeError:

        errore = (
            'Non è stato possibile verificare il pagamento. '
            'Riprova più tardi o contatta il supporto.'
        )

    return render(
        request,
        'billing/success.html',
        {
            'studio': studio,
            'messaggio': messaggio,
            'errore': errore,
        }
    )
