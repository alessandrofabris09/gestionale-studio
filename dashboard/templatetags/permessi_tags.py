from django import template

from studi.permessi import (
    puo_vedere_parcelle,
    puo_gestire_abbonamento,
    puo_gestire_backup,
    puo_usare_agenda,
    puo_creare_pratiche,
    puo_gestire_documenti,
    puo_gestire_utenti,
    puo_gestire_alert,
)

register = template.Library()


class FakeRequest:

    def __init__(self, user):
        self.user = user


def get_ruolo_utente(user):
    """
    Recupera il ruolo dell'utente in modo sicuro.
    Restituisce None se l'utente non ha un profilo studio.
    """

    if not user or not user.is_authenticated:
        return None

    try:
        return user.profilo_studio.ruolo
    except Exception:
        return None


def utente_valido(user):
    """
    Controllo comune per tutti i filtri template.
    """

    return user and user.is_authenticated


@register.filter(name='can_view_parcelle')
def can_view_parcelle(user):
    """
    Permesso per visualizzare le parcelle.
    """

    if not utente_valido(user):
        return False

    if user.is_superuser:
        return True

    return puo_vedere_parcelle(
        FakeRequest(user)
    )


@register.filter(name='can_manage_subscription')
def can_manage_subscription(user):
    """
    Permesso per gestire abbonamento / piano FREE-PRO.
    """

    if not utente_valido(user):
        return False

    if user.is_superuser:
        return True

    return puo_gestire_abbonamento(
        FakeRequest(user)
    )


@register.filter(name='can_manage_backup')
def can_manage_backup(user):
    """
    Permesso per gestire i backup.
    """

    if not utente_valido(user):
        return False

    if user.is_superuser:
        return True

    return puo_gestire_backup(
        FakeRequest(user)
    )


@register.filter(name='can_use_agenda')
def can_use_agenda(user):
    """
    Permesso per usare agenda e scadenze.
    """

    if not utente_valido(user):
        return False

    if user.is_superuser:
        return True

    return puo_usare_agenda(
        FakeRequest(user)
    )


@register.filter(name='can_use_pratiche')
def can_use_pratiche(user):
    """
    Permesso per vedere l'area pratiche/documenti.

    L'utente può accedere se può creare pratiche
    oppure se può gestire documenti.
    """

    if not utente_valido(user):
        return False

    if user.is_superuser:
        return True

    fake_request = FakeRequest(user)

    return (
        puo_creare_pratiche(fake_request) or
        puo_gestire_documenti(fake_request)
    )


@register.filter(name='can_manage_users')
def can_manage_users(user):
    """
    Permesso per gestire gli utenti dello studio.
    """

    if not utente_valido(user):
        return False

    if user.is_superuser:
        return True

    return puo_gestire_utenti(
        FakeRequest(user)
    )


@register.filter(name='can_manage_alert')
def can_manage_alert(user):
    """
    Permesso per gestire gli alert delle scadenze.
    """

    if not utente_valido(user):
        return False

    if user.is_superuser:
        return True

    return puo_gestire_alert(
        FakeRequest(user)
    )