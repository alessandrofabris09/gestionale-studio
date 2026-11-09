from decimal import Decimal
from uuid import uuid4

from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import localdate

from clienti.models import Cliente
from immobili.models import Immobile
from pratiche.models import Pratica
from studi.models import Studio


class PercorsoLancioTests(TestCase):
    def invia_modulo(self, nome, dati, *args):
        risposta = self.client.post(reverse(nome, args=args), dati)
        errori = risposta.context['form'].errors if risposta.status_code == 200 else ''
        self.assertEqual(risposta.status_code, 302, errori)
        return risposta

    def test_nuovo_studio_dalla_registrazione_al_saldo(self):
        oggi = localdate().isoformat()
        password = 'Collaudo!2026-primo-studio'
        self.invia_modulo('registrazione_studio', {
            'nome_studio': 'Studio pilota fittizio', 'username': 'studio_pilota',
            'email': 'pilota@example.test', 'password': password, 'conferma_password': password,
        })
        studio = Studio.objects.get(titolare__username='studio_pilota')
        self.assertEqual(studio.stato_abbonamento, 'TRIAL')

        self.invia_modulo('nuovo_cliente', {'nome': 'Cliente fittizio'})
        cliente = Cliente.objects.get(studio=studio)
        self.invia_modulo('nuovo_immobile', {'cliente': cliente.pk, 'comune': 'Comune di prova'})
        immobile = Immobile.objects.get(studio=studio)
        self.invia_modulo('nuova_pratica', {
            'cliente': cliente.pk, 'immobile': immobile.pk, 'tipo_pratica': 'CILA',
            'oggetto': 'Pratica pilota', 'comune': immobile.comune, 'stato': 'IN_CORSO',
            'scadenza': oggi,
        })
        pratica = Pratica.objects.get(studio=studio)
        fase = pratica.workflow_pratica.fasi_pratica.first()
        self.assertIsNotNone(fase)
        self.invia_modulo('toggle_fase', {}, fase.pk)
        fase.refresh_from_db()
        self.assertTrue(fase.completata)
        self.assertTrue(pratica.scadenze.filter(da_pratica=True, data_scadenza=oggi).exists())

        self.invia_modulo('nuova_voce_ora', {
            'data': oggi, 'tipo_attivita': 'SOPRALLUOGO', 'ore': '2', 'tariffa_oraria': '50',
            'fatturabile': 'on',
        }, pratica.pk)
        self.invia_modulo('genera_parcella_da_ore', {}, pratica.pk)
        parcella = pratica.parcelle.get()
        self.assertEqual(parcella.importo, Decimal('100'))
        self.assertEqual(parcella.voci_ore.count(), 1)
        pdf = self.client.get(reverse('pdf_parcella', args=[parcella.pk]))
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf.headers['Content-Type'], 'application/pdf')

        for importo in (Decimal('40'), parcella.saldo_residuo - Decimal('40')):
            self.invia_modulo('storico_incassi', {
                'chiave': uuid4(), 'data': oggi, 'importo': str(importo),
            }, parcella.pk)
        parcella.refresh_from_db()
        self.assertEqual(parcella.saldo_residuo, 0)
        self.assertEqual(parcella.stato, 'PAGATO')
        self.assertEqual(parcella.incassi.count(), 2)
