from django.conf import settings


def candidatura_beta_pro(request):
    return {
        'lancio_beta_free': settings.LANCIO_BETA_FREE,
        'candidatura_beta_pro_url': '' if settings.LANCIO_BETA_FREE else settings.BETA_PRO_CANDIDATURA_URL,
    }
