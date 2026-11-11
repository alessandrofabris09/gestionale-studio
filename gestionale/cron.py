import logging
from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.http import HttpResponse
from django.utils.crypto import constant_time_compare
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


logger = logging.getLogger(__name__)


@csrf_exempt
@never_cache
@require_POST
def esegui_cron(request, comando, configurazione_token):
    token = getattr(settings, configurazione_token)
    if not token or not constant_time_compare(request.headers.get('Authorization', ''), f'Bearer {token}'):
        return HttpResponse(status=404)

    try:
        call_command(comando, stdout=StringIO())
    except CommandError:
        logger.exception('Esecuzione programmata non riuscita: %s', comando)
        return HttpResponse(status=503)
    return HttpResponse(status=204)
