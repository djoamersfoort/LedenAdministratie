# Generated by Django 2.1.5 on 2019-02-15 17:00

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("LedenAdministratie", "0005_auto_20190215_1756"),
    ]

    operations = [
        migrations.RenameField(
            model_name="member",
            old_name="mobiel",
            new_name="telnr_ouders",
        ),
        migrations.RemoveField(
            model_name="member",
            name="mobiel_ouders",
        ),
    ]
