# Generated by Django 4.0.3 on 2022-07-05 13:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('appmacgest', '0001_initial'),
        ('appuser', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='proprietaire',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appuser.utilisateur'),
        ),
    ]
