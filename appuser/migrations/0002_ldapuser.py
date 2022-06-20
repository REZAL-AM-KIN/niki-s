# Generated by Django 4.0.3 on 2022-06-20 11:16

from django.db import migrations
import ldapdb.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('appuser', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LdapUser',
            fields=[
                ('dn', ldapdb.models.fields.CharField(max_length=200, primary_key=True, serialize=False)),
                ('last_modified', ldapdb.models.fields.DateTimeField(db_column='modifyTimestamp', editable=False)),
                ('first_name', ldapdb.models.fields.CharField(db_column='givenName', max_length=200, verbose_name='Prime name')),
                ('last_name', ldapdb.models.fields.CharField(db_column='sn', max_length=200, verbose_name='Final name')),
                ('full_name', ldapdb.models.fields.CharField(db_column='cn', max_length=200)),
                ('email', ldapdb.models.fields.CharField(db_column='mail', max_length=200)),
                ('password', ldapdb.models.fields.CharField(db_column='userPassword', max_length=200)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
