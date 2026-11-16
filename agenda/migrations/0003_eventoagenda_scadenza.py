import django.db.models.deletion
from django.db import migrations, models


def collega_eventi_esistenti(apps, schema_editor):
    db = schema_editor.connection.alias
    EventoAgenda = apps.get_model('agenda', 'EventoAgenda')
    Scadenza = apps.get_model('scadenze', 'Scadenza')
    eventi = EventoAgenda.objects.using(db).filter(
        tipo='SCADENZA',
        pratica__isnull=False,
        descrizione__startswith='Scadenza collegata alla pratica: ',
        ora_inizio__isnull=True,
        ora_fine__isnull=True,
        assegnato_a__isnull=True,
    ).select_related('pratica')
    scadenze = Scadenza.objects.using(db).filter(
        da_pratica=False, archiviata=False,
        workflow_origine__isnull=True, fase_origine__isnull=True,
    )

    for evento in eventi.iterator():
        if evento.studio_id != evento.pratica.studio_id:
            continue
        possibili_eventi = eventi.filter(
            studio_id=evento.studio_id, pratica_id=evento.pratica_id,
            titolo=evento.titolo, data=evento.data,
        )
        if possibili_eventi.count() != 1 or not evento.titolo.startswith('Scadenza: '):
            continue
        titolo = evento.titolo.removeprefix('Scadenza: ')
        candidati = list(scadenze.filter(
            pratica_id=evento.pratica_id, titolo=titolo, data_scadenza=evento.data,
        )[:2])
        if len(candidati) != 1:
            continue
        scadenza = candidati[0]
        EventoAgenda.objects.using(db).filter(pk=evento.pk).update(
            scadenza_id=scadenza.pk,
            priorita=scadenza.priorita,
            completato=scadenza.completata,
            cliente_id=evento.pratica.cliente_id,
        )


class Migration(migrations.Migration):
    dependencies = [
        ('agenda', '0002_eventoagenda_studio'),
        ('scadenze', '0004_scadenza_fase_origine'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventoagenda',
            name='scadenza',
            field=models.OneToOneField(
                editable=False, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='evento_agenda', to='scadenze.scadenza',
            ),
        ),
        migrations.RunPython(collega_eventi_esistenti, migrations.RunPython.noop),
    ]
