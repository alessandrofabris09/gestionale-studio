import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [('studi', '0004_studio_stripe_checkout_pending')]

    operations = [
        migrations.CreateModel(
            name='IscrizioneFreeLancio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('iscritta_il', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('studio', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='studi.studio')),
            ],
            options={
                'ordering': ('iscritta_il', 'pk'),
                'verbose_name': 'iscrizione Free al lancio',
                'verbose_name_plural': 'iscrizioni Free al lancio',
            },
        ),
    ]
