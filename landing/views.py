from django.conf import settings
from django.shortcuts import render, redirect


def home(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')

    return render(request, 'landing/home.html', {'app_url': settings.SITE_URL.rstrip('/')})


def privacy_policy(request):
    return render(request, "landing/privacy.html")


def cookie_policy(request):
    return render(request, "landing/cookie.html")


def termini(request):
    return render(request, "landing/termini.html")