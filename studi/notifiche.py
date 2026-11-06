def get_email_notifiche_studio(studio):
    """
    Restituisce l'email corretta a cui inviare le notifiche dello studio.

    Priorità:
    1. email dello studio
    2. email del titolare
    3. None se non disponibile
    """

    if not studio:
        return None

    if studio.email:
        return studio.email

    if studio.titolare and studio.titolare.email:
        return studio.titolare.email

    return None