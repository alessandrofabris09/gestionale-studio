import stripe

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from studi.utils import get_studio_utente
from studi.models import Studio

@csrf_exempt
def stripe_webhook(request):

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

    if event['type'] == 'checkout.session.completed':

        session = event['data']['object']

        metadata = session['metadata']

        studio_id = metadata['studio_id']

        if studio_id:

            try:

                studio = Studio.objects.get(
                    id=studio_id
                )

                studio.piano = 'PRO'

                studio.stato_abbonamento = 'ATTIVO'

                studio.stripe_customer_id = session['customer']

                studio.stripe_subscription_id = session['subscription']

                studio.limite_pratiche = 999999

                studio.limite_utenti = 999999

                studio.limite_storage_mb = 50000

                studio.save()

            except Studio.DoesNotExist:
                pass

    return HttpResponse(status=200)

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def checkout_pro(request):

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
            'studio_id': studio.id,
            'user_id': request.user.id,
        }
    )

    return redirect(
        session.url,
        permanent=False
    )


@login_required
def checkout_success(request):

    studio = get_studio_utente(request)

    return render(
        request,
        'billing/success.html',
        {
            'studio': studio
        }
    )