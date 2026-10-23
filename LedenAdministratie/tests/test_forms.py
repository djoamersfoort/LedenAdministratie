import io
from datetime import date
from decimal import Decimal
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from LedenAdministratie.forms import (
    ExportForm,
    InvoiceLineForm,
    InvoiceSearchForm,
    LidNoteForm,
    MemberForm,
    SettingsForm,
    StripcardForm,
)
from LedenAdministratie.models import Invoice, Member, MemberType

FAST_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class FormsTests(TestCase):
    def setUp(self):
        self.type_member = MemberType.objects.create(slug="member", display_name="Lid")
        self.member = Member.objects.create(
            first_name="Form",
            last_name="Tester",
            gebdat=date(2005, 1, 1),
            geslacht="m",
            email_address="formtester@example.com",
            straat="Straat 1",
            postcode="1234 AB",
            woonplaats="Amersfoort",
            telnr_ouders="0612345678",
            email_ouders="parents@example.com",
            aanmeld_datum=date(2020, 1, 1),
        )

    def test_member_form_valid(self):
        data = {
            "first_name": "New",
            "last_name": "Member",
            "gebdat": "15-05-2005",
            "geslacht": "v",
            "types": [self.type_member.pk],
            "email_address": "newmember@example.com",
            "straat": "Nieuwestraat 2",
            "postcode": "5678 CD",
            "woonplaats": "Utrecht",
            "telnr": "0611223344",
            "telnr_ouders": "0699887766",
            "email_ouders": "ouders@example.com",
            "aanmeld_datum": "01-01-2021",
            "days": 1,
            "media_toestemming": 1,
        }
        form = MemberForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        saved_member = form.save()
        self.assertEqual(saved_member.first_name, "New")
        self.assertEqual(saved_member.last_name, "Member")

    def test_member_form_with_foto_upload(self):
        img = Image.new("RGB", (20, 20), color="red")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        image_bytes = buf.getvalue()

        data = {
            "first_name": "Photo",
            "last_name": "Member",
            "gebdat": "15-05-2005",
            "geslacht": "m",
            "types": [self.type_member.pk],
            "email_address": "photomember@example.com",
            "straat": "Straat 3",
            "postcode": "1234 AB",
            "woonplaats": "Amersfoort",
            "telnr_ouders": "0612345678",
            "email_ouders": "parents@example.com",
            "aanmeld_datum": "01-01-2021",
            "days": 1,
            "media_toestemming": 1,
        }
        uploaded = SimpleUploadedFile("test.png", image_bytes, content_type="image/png")
        form = MemberForm(data=data, files={"foto": uploaded})
        self.assertTrue(form.is_valid(), form.errors)
        saved_member = form.save()
        self.assertEqual(saved_member.foto, image_bytes)

    def test_invoice_search_form_valid(self):
        invoice = Invoice.objects.create(
            member=self.member,
            amount=Decimal("120.00"),
            amount_payed=Decimal("0.00"),
        )
        form = InvoiceSearchForm(data={"invoice_number": str(invoice.pk)})
        self.assertTrue(form.is_valid())

    def test_invoice_search_form_invalid(self):
        form = InvoiceSearchForm(data={"invoice_number": "999999"})
        self.assertFalse(form.is_valid())
        self.assertIn("invoice_number", form.errors)

    def test_invoice_line_form(self):
        form = InvoiceLineForm(
            data={"description": "Test line", "count": 2, "amount": "15.50"}
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["count"], 2)
        self.assertEqual(form.cleaned_data["amount"], Decimal("15.50"))

    def test_export_form(self):
        form = ExportForm(data={"filter_slug": str(self.type_member.pk)})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["filter_slug"], self.type_member)

    def test_lid_note_form(self):
        form = LidNoteForm(data={"text": "Note text", "done": True})
        self.assertTrue(form.is_valid())

    def test_settings_form(self):
        data = {
            "invoice_amount_year": "180.00",
            "invoice_amount_year_senior": "220.00",
            "invoice_amount_day": "7.00",
            "invoice_amount_month": "15.00",
            "invoice_amount_sponsor": "160.00",
            "welcome_pdf_location": "https://example.com/welcome.pdf",
        }
        form = SettingsForm(data=data)
        self.assertTrue(form.is_valid())

    def test_stripcard_form_initials(self):
        form = StripcardForm()
        self.assertIsNotNone(
            form.get_initial_for_field(form.fields["issue_date"], "issue_date")
        )
        self.assertIsNotNone(
            form.get_initial_for_field(
                form.fields["expiration_date"], "expiration_date"
            )
        )
        self.assertIsNotNone(form["issue_date"].value())
        self.assertIsNotNone(form["expiration_date"].value())
