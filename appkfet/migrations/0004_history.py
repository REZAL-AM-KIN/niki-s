# Generated by Django 4.0.3 on 2022-06-15 07:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('appkfet', '0003_alter_produit_entite'),
    ]

    operations = [
        migrations.CreateModel(
            name='History',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom_evenement', models.CharField(max_length=200)),
                ('prix_evenement', models.DecimalField(decimal_places=2, max_digits=5)),
                ('entite_evenement', models.CharField(max_length=200)),
                ('date_evenement', models.DateTimeField()),
                ('cible_evenement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appkfet.consommateur')),
            ],
        ),
    ]
