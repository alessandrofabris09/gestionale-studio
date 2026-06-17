from django.shortcuts import render, redirect


def home(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')

    return render(request, 'landing/home.html')


def privacy_policy(request):
    return render(request, 'landing/privacy.html')


def termini_utilizzo(request):
    return render(request, 'landing/termini.html')