# Generated by Django 4.0.3 on 2022-06-16 11:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appkfet', '0007_consommateur_totaldep'),
    ]

    operations = [
        migrations.AddField(
            model_name='consommateur',
            name='activated',
            field=models.BooleanField(default=True),
        ),
    ]
