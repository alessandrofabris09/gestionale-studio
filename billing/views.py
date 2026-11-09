from django.views.decorators.http import require_POST
from studi.permessi import puo_gestire_abbonamento
import os
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

    # =========================
    # FATTURA PAGATA
    # =========================

    elif event_type == 'invoice.paid':

        invoice = event['data']['object']

        subscription_id = abbonamento_da_fattura(invoice)

        customer_id = invoice.get(
            'customer'
        )

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

    # =========================
    # PAGAMENTO FALLITO
    # =========================

    elif event_type == 'invoice.payment_failed':

        invoice = event['data']['object']

        subscription_id = abbonamento_da_fattura(invoice)

        if subscription_id:

            try:

                studio = Studio.objects.get(
                    stripe_subscription_id=subscription_id
                )

                aggiorna_stato_abbonamento(
                    studio,
                    'SCADUTO'
                )

            except Studio.DoesNotExist:

                pass

    # =========================
    # SUBSCRIPTION AGGIORNATA
    # =========================

    elif event_type == 'customer.subscription.updated':

        subscription = event['data']['object']

        subscription_id = subscription.get(
            'id'
        )

        customer_id = subscription.get(
            'customer'
        )

        status = subscription.get(
            'status'
        )

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
                    'past_due',
                    'unpaid',
                    'incomplete',
                    'incomplete_expired',
                    'paused',
                ]:

                    aggiorna_stato_abbonamento(
                        studio,
                        'SCADUTO'
                    )

                elif status in [
                    'canceled',
                ]:

                    disattiva_piano_pro(
                        studio
                    )

            except Studio.DoesNotExist:

                pass

    # =========================
    # SUBSCRIPTION CANCELLATA
    # =========================

    elif event_type == 'customer.subscription.deleted':

        subscription = event['data']['object']

        subscription_id = subscription.get(
            'id'
        )

        if subscription_id:

            try:

                studio = Studio.objects.get(
                    stripe_subscription_id=subscription_id
                )

                disattiva_piano_pro(
                    studio
                )

            except Studio.DoesNotExist:

                pass

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

    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_PRICE_PRO_MONTHLY:

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

        try:

            stripe.Customer.modify(
                studio.stripe_customer_id,
                email=email_checkout,
                name=studio.nome,
            )

        except Exception:

            pass

        checkout_data['customer'] = studio.stripe_customer_id

    else:

        checkout_data['customer_email'] = email_checkout

    coupon_primo_anno = os.environ.get(
        'STRIPE_COUPON_PRO_FIRST_YEAR',
        ''
    )

    if coupon_primo_anno:

        checkout_data['discounts'] = [
            {
                'coupon': coupon_primo_anno
            }
        ]

    try:
        session = stripe.checkout.Session.create(**checkout_data)
    except stripe.error.StripeError:
        return render(request, 'billing/success.html', {
            'studio': studio,
            'errore': 'Il servizio di pagamento non è disponibile. Riprova più tardi.',
        })

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
