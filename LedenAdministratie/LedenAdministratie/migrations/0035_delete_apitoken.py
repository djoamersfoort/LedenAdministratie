# Generated by Django 3.2 on 2021-06-12 13:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('LedenAdministratie', '0034_member_user'),
    ]

    operations = [
        migrations.DeleteModel(
            name='APIToken',
        ),
    ]