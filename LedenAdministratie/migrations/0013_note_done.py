# Generated by Django 2.1.5 on 2019-02-22 10:43

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("LedenAdministratie", "0012_auto_20190217_1218"),
    ]

    operations = [
        migrations.AddField(
            model_name="note",
            name="done",
            field=models.BooleanField(default=False, verbose_name="Afgerond"),
        ),
    ]
