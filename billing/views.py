import stripe

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from studi.utils import get_studio_utente
from studi.models import Studio


stripe.api_key = settings.STRIPE_SECRET_KEY


def attiva_piano_pro(studio, customer_id=None, subscription_id=None):
    """
    Attiva il piano PRO per lo studio.
    Questa funzione deve essere richiamata solo dopo conferma Stripe valida.
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

    studio.limite_pratiche = 20
    studio.limite_utenti = 1
    studio.limite_storage_mb = 500

    studio.save()


@csrf_exempt
def stripe_webhook(request):
    """
    Webhook Stripe.

    Il piano PRO viene attivato solo da eventi Stripe verificati.
    La pagina success non attiva più il piano PRO.
    """

    payload = request.body

    sig_header = request.META.get(
        'HTTP_STRIPE_SIGNATURE'
    )

    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:

        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            endpoint_secret
        )

    except ValueError:

        return HttpResponse(status=400)

    except stripe.error.SignatureVerificationError:

        return HttpResponse(status=400)

    event_type = event.get('type')

    # 1. Checkout completato
    if event_type == 'checkout.session.completed':

        session = event['data']['object']

        metadata = session.get('metadata', {})

        studio_id = metadata.get('studio_id')

        mode = session.get('mode')
        payment_status = session.get('payment_status')
        subscription_id = session.get('subscription')
        customer_id = session.get('customer')

        if (
            studio_id and
            mode == 'subscription' and
            payment_status == 'paid' and
            subscription_id
        ):

            try:

                studio = Studio.objects.get(
                    id=studio_id
                )

                attiva_piano_pro(
                    studio=studio,
                    customer_id=customer_id,
                    subscription_id=subscription_id
                )

            except Studio.DoesNotExist:
                pass

    # 2. Fattura pagata: mantiene o riattiva il PRO
    elif event_type == 'invoice.paid':

        invoice = event['data']['object']

        subscription_id = invoice.get('subscription')
        customer_id = invoice.get('customer')

        if subscription_id:

            try:

                studio = Studio.objects.get(
                    stripe_subscription_id=subscription_id
                )

                attiva_piano_pro(
                    studio=studio,
                    customer_id=customer_id,
                    subscription_id=subscription_id
                )

            except Studio.DoesNotExist:
                pass

    # 3. Pagamento fallito: segnala abbonamento scaduto
    elif event_type == 'invoice.payment_failed':

        invoice = event['data']['object']

        subscription_id = invoice.get('subscription')

        if subscription_id:

            try:

                studio = Studio.objects.get(
                    stripe_subscription_id=subscription_id
                )

                studio.stato_abbonamento = 'SCADUTO'
                studio.save()

            except Studio.DoesNotExist:
                pass

    # 4. Subscription aggiornata
    elif event_type == 'customer.subscription.updated':

        subscription = event['data']['object']

        subscription_id = subscription.get('id')
        customer_id = subscription.get('customer')
        status = subscription.get('status')

        if subscription_id:

            try:

                studio = Studio.objects.get(
                    stripe_subscription_id=subscription_id
                )

                if status in [
                    'active',
                    'trialing',
                ]:

                    attiva_piano_pro(
                        studio=studio,
                        customer_id=customer_id,
                        subscription_id=subscription_id
                    )

                elif status in [
                    'canceled',
                    'unpaid',
                    'incomplete_expired',
                    'paused',
                ]:

                    disattiva_piano_pro(studio)

            except Studio.DoesNotExist:
                pass

    # 5. Subscription cancellata
    elif event_type == 'customer.subscription.deleted':

        subscription = event['data']['object']

        subscription_id = subscription.get('id')

        if subscription_id:

            try:

                studio = Studio.objects.get(
                    stripe_subscription_id=subscription_id
                )

                disattiva_piano_pro(studio)

            except Studio.DoesNotExist:
                pass

    return HttpResponse(status=200)


@login_required
def checkout_pro(request):
    """
    Crea la sessione Stripe Checkout per passare al piano PRO.
    """

    studio = get_studio_utente(request)

    if not studio:
        return redirect('login')

    session = stripe.checkout.Session.create(
        mode='subscription',

        customer_email=request.user.email,

        line_items=[
            {
                'price': settings.STRIPE_PRICE_PRO_MONTHLY,
                'quantity': 1,
            }
        ],

        success_url=settings.SITE_URL + '/billing/success/',
        cancel_url=settings.SITE_URL + '/studi/abbonamento/',

        metadata={
            'studio_id': str(studio.id),
            'user_id': str(request.user.id),
        },

        subscription_data={
            'metadata': {
                'studio_id': str(studio.id),
                'user_id': str(request.user.id),
            }
        }
    )

    return redirect(
        session.url,
        permanent=False
    )


@login_required
def checkout_success(request):
    """
    Pagina di ritorno dopo Stripe Checkout.

    Non attiva il piano PRO.
    L'attivazione avviene solo tramite webhook Stripe verificato.
    """

    studio = get_studio_utente(request)

    return render(
        request,
        'billing/success.html',
        {
            'studio': studio
        }
    )