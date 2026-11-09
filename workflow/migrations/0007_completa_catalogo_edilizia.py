from django.db import migrations


GRUPPI_EDILIZIA = (
    (
        'Rilievo e stato legittimo|Inquadramento intervento, titolo e vincoli|Progetto e allegati|Deposito o avvio dell’intervento|Verifica finale',
        'Manutenzione ordinaria - verifica edilizia libera|Manutenzione straordinaria senza opere strutturali|'
        'Manutenzione straordinaria con opere strutturali|Restauro e risanamento conservativo senza opere strutturali|'
        'Restauro e risanamento conservativo con opere strutturali|Ristrutturazione edilizia senza demolizione|'
        'Nuova costruzione|Ampliamento e sopraelevazione|Ristrutturazione urbanistica|'
        'Frazionamento o accorpamento di unità immobiliari|Cambio d’uso senza opere|Cambio d’uso con opere|'
        'Demolizione senza ricostruzione|Recupero di seminterrati e locali accessori|'
        'Realizzazione di pertinenze e autorimesse|Piscine e opere pertinenziali esterne|'
        'Recinzioni, cancelli e muri di contenimento|Pergole, tende, VEPA e schermature solari|'
        'Pavimentazione e sistemazione di aree esterne|Serre e manufatti agricoli|'
        'Depositi e impianti produttivi all’aperto|Manufatti in strutture ricettive all’aperto|'
        'Impianto solare a servizio dell’edificio - verifica edilizia',
    ),
    (
        'Verifica intervento e atti di assenso|Predisposizione elaborati e modulistica|Deposito|Verifica esito e decorrenza',
        'CILA con richiesta di atti di assenso|SCIA edilizia unica|SCIA edilizia condizionata|'
        'SCIA alternativa con richiesta di atti di assenso|Permesso di costruire con atti di assenso|'
        'Attestazione di formazione del silenzio assenso sul permesso di costruire',
    ),
    (
        'Rilievo e ricostruzione documentale|Confronto tra stato rilevato e titoli|Verifica del procedimento applicabile|'
        'Relazione, elaborati e presentazione|Esito e aggiornamento fascicolo',
        'Accertamento di conformità per parziali difformità o variazioni essenziali|'
        'Regolarizzazione di varianti a titoli rilasciati prima della legge 10/1977|'
        'Fiscalizzazione dell’abuso edilizio - verifica e istanza|'
        'Ripristino a seguito di ordinanza edilizia|Condono edilizio - integrazione documentale',
    ),
    (
        'Recupero pratica originaria|Verifica stato del procedimento|Preparazione comunicazione o istanza|'
        'Trasmissione e aggiornamento fascicolo',
        'Accesso agli atti edilizi SUE|Integrazione documentale pratica edilizia|'
        'Rinuncia o archiviazione pratica edilizia|Sostituzione direttore lavori o impresa|'
        'Comunicazione fine lavori parziale|Collaudo finale SCIA edilizia|'
        'SCIA per l’agibilità di immobile esistente senza nuovi lavori|'
        'Comunicazione di rimozione di opere temporanee',
    ),
)


def aggiungi_procedimenti(apps, schema_editor):
    db = schema_editor.connection.alias
    modelli = apps.get_model('workflow', 'TipoWorkflow').objects.using(db)
    fasi = apps.get_model('workflow', 'FaseWorkflow').objects.using(db)
    esistenti = set(modelli.filter(studio__isnull=True).values_list('nome', flat=True))
    for passaggi, nomi in GRUPPI_EDILIZIA:
        for nome in nomi.split('|'):
            if nome in esistenti:
                continue
            modello = modelli.create(nome=nome, categoria='EDILIZIA', attivo=True)
            fasi.bulk_create([
                fasi.model(workflow_id=modello.pk, titolo=titolo, ordine=ordine)
                for ordine, titolo in enumerate(passaggi.split('|'), start=1)
            ])


class Migration(migrations.Migration):
    dependencies = [('workflow', '0006_catalogo_pratiche')]
    operations = [migrations.RunPython(aggiungi_procedimenti, migrations.RunPython.noop)]
