# Generated by Django 3.2.13 on 2022-05-26 10:22

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("LedenAdministratie", "0037_alter_member_days"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Email",
        ),
    ]
