from django.db import migrations, models
from django.db.models import deletion


class Migration(migrations.Migration):
    dependencies = [
        ('ore', '0001_initial'),
        ('parcelle', '0003_alter_parcella_options_parcella_aliquota_cassa_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='voceora',
            old_name='inserita_in_parcella',
            new_name='fatturazione_storica',
        ),
        migrations.AddField(
            model_name='voceora',
            name='parcella',
            field=models.ForeignKey(
                to='parcelle.parcella', on_delete=deletion.SET_NULL, null=True, blank=True,
                editable=False, related_name='voci_ore',
            ),
        ),
    ]
