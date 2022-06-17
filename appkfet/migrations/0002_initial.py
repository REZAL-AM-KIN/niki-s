# Generated by Django 3.2.8 on 2021-10-09 17:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('appkfet', '0001_initial'),
        ('appuser', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='consommateur',
            name='consommateur',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appuser.utilisateur'),
        ),
        migrations.AddField(
            model_name='bucquage',
            name='cible_bucquage',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appkfet.consommateur'),
        ),
    ]
