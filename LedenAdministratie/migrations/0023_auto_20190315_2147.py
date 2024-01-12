# Generated by Django 2.1.7 on 2019-03-15 20:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("LedenAdministratie", "0022_invoice_smtp_error"),
    ]

    operations = [
        migrations.AlterField(
            model_name="invoice",
            name="member",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="invoices",
                to="LedenAdministratie.Member",
            ),
        ),
    ]
