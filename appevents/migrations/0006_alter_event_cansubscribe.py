# Generated by Django 4.0.3 on 2022-06-16 15:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appevents', '0005_alter_participation_event_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='cansubscribe',
            field=models.BooleanField(default=True, verbose_name="Ouvert à l'inscription"),
        ),
    ]
