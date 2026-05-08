from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

from scadenze.models import Scadenza


class Command(BaseCommand):
    help = 'Invia email per scadenze scadute e imminenti'

    def handle(self, *args, **kwargs):

        oggi = date.today()
        limite = oggi + timedelta(days=7)

        scadenze = Scadenza.objects.filter(
            completata=False,
            data_scadenza__lte=limite
        ).order_by('data_scadenza')

        if not scadenze.exists():
            self.stdout.write(
                self.style.SUCCESS('Nessuna scadenza da notificare.')
            )
            return

        messaggio = 'Alert scadenze gestionale studio tecnico\n\n'

        for scadenza in scadenze:

            if scadenza.data_scadenza < oggi:
                stato = 'SCADUTA'
            else:
                stato = 'IMMINENTE'

            messaggio += (
                f'- {stato}: {scadenza.titolo}\n'
                f'  Data: {scadenza.data_scadenza}\n'
                f'  Pratica: {scadenza.pratica}\n'
                f'  Priorità: {scadenza.priorita}\n\n'
            )

        send_mail(
            subject='Alert scadenze - Gestionale Studio Tecnico',
            message=messaggio,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ALERT_EMAIL],
            fail_silently=False,
        )

        self.stdout.write(
            self.style.SUCCESS('Email alert scadenze inviata correttamente.')
        )