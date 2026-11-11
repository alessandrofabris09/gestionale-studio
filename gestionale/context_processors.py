from django.conf import settings


def candidatura_beta_pro(request):
    return {'candidatura_beta_pro_url': settings.BETA_PRO_CANDIDATURA_URL}
