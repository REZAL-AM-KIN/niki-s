# Generated by Django 4.0.3 on 2022-06-16 11:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appevents', '0004_remove_event_date_fermeture_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participation_event',
            name='number',
            field=models.IntegerField(default=1, verbose_name='Quantité'),
        ),
    ]
