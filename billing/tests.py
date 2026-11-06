import hashlib
import hmac
import json
import time
from types import SimpleNamespace
from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from studi.models import Studio, ProfiloUtente


@override_settings(STRIPE_SECRET_KEY='sk_test_fittizia', STRIPE_PRICE_PRO_MONTHLY='price_fittizio')
class CheckoutProtezioneTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('qa_checkout')
        self.studio = Studio.objects.create(nome='QA checkout', titolare=self.owner, stato_abbonamento='ATTIVO')
        self.profile = ProfiloUtente.objects.create(user=self.owner, studio=self.studio, ruolo='TITOLARE')
        self.client.force_login(self.owner)

    def test_get_non_crea_sessioni_o_modifica_cliente(self):
        with patch('billing.views.stripe.checkout.Session.create') as create, patch('billing.views.stripe.Customer.modify') as modify:
            self.assertEqual(self.client.get('/billing/checkout/pro/').status_code, 405)
            create.assert_not_called()
            modify.assert_not_called()

    def test_post_senza_csrf_bloccato(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        with patch('billing.views.stripe.checkout.Session.create') as create:
            self.assertEqual(client.post('/billing/checkout/pro/').status_code, 403)
            create.assert_not_called()

    def test_titolare_checkout_con_studio_corretto(self):
        with patch('billing.views.stripe.checkout.Session.create', return_value=SimpleNamespace(url='https://checkout.stripe.com/qa')) as create:
            response = self.client.post('/billing/checkout/pro/', {'studio_id': '99999'})
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response['Location'], 'https://checkout.stripe.com/qa')
            self.assertEqual(create.call_args.kwargs['metadata']['studio_id'], str(self.studio.pk))

    def test_altri_ruoli_non_avviano_checkout(self):
        for role in ['TECNICO', 'SEGRETERIA', 'COLLABORATORE']:
            self.profile.ruolo = role
            self.profile.save()
            with self.subTest(role=role), patch('billing.views.stripe.checkout.Session.create') as create:
                self.assertEqual(self.client.post('/billing/checkout/pro/').status_code, 403)
                create.assert_not_called()

    def test_pulsante_abbonamento_usa_post(self):
        response = self.client.get('/studi/abbonamento/')
        self.assertContains(response, 'action="/billing/checkout/pro/"')
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_ritorno_checkout_non_riattiva_abbonamento_annullato(self):
        self.studio.piano = 'FREE'
        self.studio.stato_abbonamento = 'ANNULLATO'
        self.studio.save()
        session = SimpleNamespace(metadata={'studio_id': str(self.studio.pk)}, mode='subscription', status='complete', payment_status='paid', subscription='sub_vecchia', customer='cus_vecchio')
        with patch('billing.views.stripe.checkout.Session.retrieve', return_value=session), patch('billing.views.attiva_piano_pro') as activate:
            response = self.client.get('/billing/success/?session_id=cs_vecchia')
            self.assertEqual(response.status_code, 200)
            activate.assert_not_called()
        self.studio.refresh_from_db()
        self.assertEqual(self.studio.piano, 'FREE')
        self.assertEqual(self.studio.stato_abbonamento, 'ANNULLATO')

    def test_errore_checkout_mostra_messaggio_senza_dettagli_tecnici(self):
        import stripe
        with patch('billing.views.stripe.checkout.Session.create', side_effect=stripe.error.APIConnectionError('Dettaglio tecnico fittizio')):
            response = self.client.post('/billing/checkout/pro/')
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, 'Dettaglio tecnico fittizio')

    @override_settings(STRIPE_WEBHOOK_SECRET='whsec_fittizio')
    def test_webhook_verificato_attiva_piano(self):
        event = {
            'id': 'evt_fittizio',
            'object': 'event',
            'type': 'checkout.session.completed',
            'data': {'object': {
                'metadata': {'studio_id': str(self.studio.pk)},
                'mode': 'subscription',
                'payment_status': 'paid',
                'subscription': 'sub_fittizia',
                'customer': 'cus_fittizio',
            }},
        }
        payload = json.dumps(event)
        timestamp = int(time.time())
        signature = hmac.new(
            b'whsec_fittizio', f'{timestamp}.{payload}'.encode(), hashlib.sha256
        ).hexdigest()
        response = self.client.post(
            '/billing/webhook/', payload, content_type='application/json',
            HTTP_STRIPE_SIGNATURE=f't={timestamp},v1={signature}',
        )
        self.assertEqual(response.status_code, 200)
        self.studio.refresh_from_db()
        self.assertEqual(self.studio.piano, 'PRO')
        self.assertEqual(self.studio.stato_abbonamento, 'ATTIVO')
        self.assertEqual(self.studio.stripe_subscription_id, 'sub_fittizia')

    def test_token_valido_consente_checkout(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        client.get('/studi/abbonamento/')
        token = client.cookies['csrftoken'].value
        with patch('billing.views.stripe.checkout.Session.create', return_value=SimpleNamespace(url='https://checkout.stripe.com/qa')) as create:
            response = client.post('/billing/checkout/pro/', {'csrfmiddlewaretoken': token})
            self.assertEqual(response.status_code, 302)
            create.assert_called_once()

    def test_upgrade_tecnico_non_mostra_checkout(self):
        from django.template.loader import render_to_string
        from django.test import RequestFactory
        self.profile.ruolo = 'TECNICO'
        self.profile.save()
        request = RequestFactory().get('/pratiche/nuova/')
        request.user = User.objects.get(pk=self.owner.pk)
        html = render_to_string('studi/upgrade_required.html', {'studio': self.studio}, request=request)
        self.assertNotIn('action="/billing/checkout/pro/"', html)
        self.assertIn('Chiedi al titolare', html)
