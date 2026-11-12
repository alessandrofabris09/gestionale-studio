from django.http import Http404, HttpResponse
from django.views.decorators.http import require_safe


DOMINIO_PUBBLICO = 'studiotecnicocloud.it'
URL_CANONICO = f'https://{DOMINIO_PUBBLICO}/'
HOST_PUBBLICI = {DOMINIO_PUBBLICO, f'www.{DOMINIO_PUBBLICO}', f'app.{DOMINIO_PUBBLICO}'}


def _host(request):
    return request.get_host().partition(':')[0].lower().rstrip('.')


@require_safe
def robots(request):
    host = _host(request)
    if host == DOMINIO_PUBBLICO:
        testo = f'User-agent: *\nDisallow:\nSitemap: {URL_CANONICO}sitemap.xml\n'
    elif host in HOST_PUBBLICI:
        testo = 'User-agent: *\nDisallow:\n'
    else:
        testo = 'User-agent: *\nDisallow: /\n'
    return HttpResponse(testo, content_type='text/plain; charset=utf-8')


@require_safe
def sitemap(request):
    if _host(request) != DOMINIO_PUBBLICO:
        raise Http404
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'  <url><loc>{URL_CANONICO}</loc></url>\n'
        '</urlset>\n'
    )
    return HttpResponse(xml, content_type='application/xml; charset=utf-8')
