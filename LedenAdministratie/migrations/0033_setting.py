# Generated by Django 3.0.2 on 2020-03-14 10:20

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("LedenAdministratie", "0032_auto_20190705_1020"),
    ]

    operations = [
        migrations.CreateModel(
            name="Setting",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50)),
                ("value", models.CharField(blank=True, max_length=1024, null=True)),
            ],
        ),
    ]
