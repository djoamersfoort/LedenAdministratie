# Generated by Django 2.2.2 on 2019-06-10 08:13

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("LedenAdministratie", "0027_auto_20190602_1048"),
    ]

    operations = [
        migrations.AlterField(
            model_name="member",
            name="email_ouders",
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name="member",
            name="telnr_ouders",
            field=models.CharField(max_length=30),
        ),
    ]
