from django.contrib.auth.models import Group
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.utils import timezone

from datetime import timedelta

from studi.models import Studio, ProfiloUtente

from .forms import RegistrazioneStudioForm


def registrazione_studio(request):

    if request.user.is_authenticated:

        return redirect('home')

    if request.method == 'POST':

        form = RegistrazioneStudioForm(request.POST)

        if form.is_valid():

            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )

            user.first_name = form.cleaned_data['nome_studio']
            user.save()

            admin_group, created = Group.objects.get_or_create(
                name='Admin Studio'
            )

            user.groups.add(admin_group)
            
            studio = Studio.objects.create(
                nome=form.cleaned_data['nome_studio'],
                titolare=user,
                email=form.cleaned_data['email'],
                telefono=form.cleaned_data.get('telefono', ''),
                partita_iva=form.cleaned_data.get('partita_iva', ''),
                attivo=True,
                piano='FREE',
                stato_abbonamento='TRIAL',
                trial_fino_al=timezone.now().date() + timedelta(days=14),
                limite_pratiche=20,
                limite_utenti=1,
                limite_storage_mb=500
            )

            ProfiloUtente.objects.create(
                user=user,
                studio=studio,
                ruolo='TITOLARE'
            )

            login(request, user)

            return redirect('home')

    else:

        form = RegistrazioneStudioForm()

    return render(
        request,
        'utenti/registrazione_studio.html',
        {
            'form': form
        }
    )