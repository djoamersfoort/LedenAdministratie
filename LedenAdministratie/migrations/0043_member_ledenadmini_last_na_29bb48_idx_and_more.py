# Generated by Django 5.0.4 on 2024-05-05 08:46

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("LedenAdministratie", "0042_stripcard_used"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddIndex(
            model_name="member",
            index=models.Index(
                fields=["last_name", "first_name"],
                name="LedenAdmini_last_na_29bb48_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="member",
            index=models.Index(
                fields=["first_name"], name="LedenAdmini_first_n_586162_idx"
            ),
        ),
    ]
