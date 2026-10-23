from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings

from LedenAdministratie.invoice import InvoiceLine, InvoiceTool, InvoiceType
from LedenAdministratie.models import Member, MemberType, Invoice, Setting

FAST_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class InvoiceToolTests(TestCase):
    def setUp(self):
        self.type_member = MemberType.objects.create(slug="member", display_name="Lid")
        self.type_senior = MemberType.objects.create(
            slug="senior", display_name="Senior Lid"
        )
        self.type_sponsor = MemberType.objects.create(
            slug="sponsor", display_name="Sponsor"
        )
        self.type_stripcard = MemberType.objects.create(
            slug="strippenkaart", display_name="Strippenkaart"
        )

        Setting.objects.create(name="invoice_amount_year", value="120.00")
        Setting.objects.create(name="invoice_amount_year_senior", value="90.00")
        Setting.objects.create(name="invoice_amount_month", value="10.00")
        Setting.objects.create(name="invoice_amount_day", value="5.00")
        Setting.objects.create(name="invoice_amount_sponsor", value="250.00")

    def create_member(self, **kwargs):
        defaults = {
            "first_name": "Test",
            "last_name": "Lid",
            "gebdat": date(2005, 1, 1),
            "geslacht": "m",
            "email_address": "test@example.com",
            "straat": "Straat 1",
            "postcode": "1234 AB",
            "woonplaats": "Amersfoort",
            "telnr_ouders": "0612345678",
            "email_ouders": "ouders@example.com",
            "aanmeld_datum": date(date.today().year, 1, 15),
            "days": 1,
        }
        defaults.update(kwargs)
        return Member.objects.create(**defaults)

    def test_invoice_line_total(self):
        line = InvoiceLine(count=2, amount=Decimal("15.50"), description="Test line")
        self.assertEqual(line.line_total, Decimal("31.00"))

    def test_calculate_grand_total(self):
        lines = [
            InvoiceLine(count=1, amount=Decimal("120.00"), description="Contributie"),
            InvoiceLine(count=2, amount=Decimal("15.00"), description="Extra"),
        ]
        self.assertEqual(InvoiceTool.calculate_grand_total(lines), Decimal("150.00"))

    def test_get_title_for_invoice_type(self):
        self.assertEqual(
            InvoiceTool.get_title_for_invoice_type(InvoiceType.STANDARD),
            "Aan de ouders/verzorgers van:",
        )
        self.assertEqual(
            InvoiceTool.get_title_for_invoice_type(InvoiceType.STRIPCARD),
            "Aan de ouders/verzorgers van:",
        )
        self.assertEqual(
            InvoiceTool.get_title_for_invoice_type(InvoiceType.TWO_DAYS),
            "Aan de ouders/verzorgers van:",
        )
        self.assertEqual(
            InvoiceTool.get_title_for_invoice_type(InvoiceType.MARCH),
            "Aan de ouders/verzorgers van:",
        )
        self.assertEqual(
            InvoiceTool.get_title_for_invoice_type(InvoiceType.SENIOR),
            "Aan:",
        )
        self.assertEqual(
            InvoiceTool.get_title_for_invoice_type(InvoiceType.SPONSOR),
            "Aan:",
        )
        self.assertEqual(
            InvoiceTool.get_title_for_invoice_type(InvoiceType.CUSTOM),
            "Aan:",
        )

    def test_get_defaults_standard(self):
        defaults = InvoiceTool.get_defaults_for_invoice_type(InvoiceType.STANDARD)
        self.assertEqual(len(defaults), 1)
        self.assertEqual(defaults[0]["amount"], Decimal("120.00"))
        self.assertEqual(defaults[0]["count"], 1)

    def test_get_defaults_senior(self):
        defaults = InvoiceTool.get_defaults_for_invoice_type(InvoiceType.SENIOR)
        self.assertEqual(len(defaults), 1)
        self.assertEqual(defaults[0]["amount"], Decimal("90.00"))

    def test_get_defaults_march(self):
        member = self.create_member(aanmeld_datum=date(date.today().year, 5, 10))
        defaults = InvoiceTool.get_defaults_for_invoice_type(
            InvoiceType.MARCH, member=member
        )
        self.assertEqual(len(defaults), 2)
        self.assertEqual(defaults[0]["amount"], Decimal("120.00"))
        # month 5 means -(5 - 1) = -4 months correction
        self.assertEqual(defaults[1]["count"], -4)
        self.assertEqual(defaults[1]["amount"], Decimal("10.00"))

    def test_get_defaults_stripcard(self):
        defaults = InvoiceTool.get_defaults_for_invoice_type(InvoiceType.STRIPCARD)
        self.assertEqual(len(defaults), 1)
        self.assertEqual(defaults[0]["count"], 10)
        self.assertEqual(defaults[0]["amount"], Decimal("5.00"))

    def test_get_defaults_sponsor(self):
        defaults = InvoiceTool.get_defaults_for_invoice_type(InvoiceType.SPONSOR)
        self.assertEqual(len(defaults), 1)
        self.assertEqual(defaults[0]["amount"], Decimal("250.00"))

    def test_get_defaults_two_days(self):
        defaults = InvoiceTool.get_defaults_for_invoice_type(InvoiceType.TWO_DAYS)
        self.assertEqual(len(defaults), 2)
        self.assertEqual(defaults[0]["amount"], Decimal("120.00"))
        self.assertEqual(defaults[1]["amount"], Decimal("60.00"))

    def test_get_defaults_custom(self):
        defaults = InvoiceTool.get_defaults_for_invoice_type(InvoiceType.CUSTOM)
        self.assertEqual(defaults, [])

    def test_get_members_invoice_type_filters(self):
        current_year = date.today().year

        # Standard active member (registered before March 1st)
        m_standard = self.create_member(
            email_address="standard@example.com",
            aanmeld_datum=date(current_year, 1, 15),
        )
        m_standard.types.add(self.type_member)

        # March member (registered after Feb 28th)
        m_march = self.create_member(
            email_address="march@example.com", aanmeld_datum=date(current_year, 3, 15)
        )
        m_march.types.add(self.type_member)

        # Senior member
        m_senior = self.create_member(email_address="senior@example.com")
        m_senior.types.add(self.type_senior)

        # Sponsor member
        m_sponsor = self.create_member(email_address="sponsor@example.com")
        m_sponsor.types.add(self.type_sponsor)

        # Stripcard member
        m_stripcard = self.create_member(email_address="strip@example.com")
        m_stripcard.types.add(self.type_stripcard)

        # Two days member
        m_twodays = self.create_member(email_address="two@example.com", days=2)
        m_twodays.types.add(self.type_member)

        # Inactive member
        m_inactive = self.create_member(
            email_address="inactive@example.com",
            afmeld_datum=date.today() - timedelta(days=1),
        )
        m_inactive.types.add(self.type_member)

        standard_qs = InvoiceTool.get_members_invoice_type(InvoiceType.STANDARD)
        self.assertIn(m_standard, standard_qs)
        self.assertNotIn(m_march, standard_qs)
        self.assertNotIn(m_twodays, standard_qs)
        self.assertNotIn(m_inactive, standard_qs)

        senior_qs = InvoiceTool.get_members_invoice_type(InvoiceType.SENIOR)
        self.assertIn(m_senior, senior_qs)
        self.assertNotIn(m_standard, senior_qs)

        march_qs = InvoiceTool.get_members_invoice_type(InvoiceType.MARCH)
        self.assertIn(m_march, march_qs)
        self.assertNotIn(m_standard, march_qs)

        sponsor_qs = InvoiceTool.get_members_invoice_type(InvoiceType.SPONSOR)
        self.assertIn(m_sponsor, sponsor_qs)

        stripcard_qs = InvoiceTool.get_members_invoice_type(InvoiceType.STRIPCARD)
        self.assertIn(m_stripcard, stripcard_qs)

        twodays_qs = InvoiceTool.get_members_invoice_type(InvoiceType.TWO_DAYS)
        self.assertIn(m_twodays, twodays_qs)

    def test_create_email_recipients(self):
        member = self.create_member(
            email_address="child@example.com",
            email_ouders="parent1@example.com,parent2@example.com",
        )
        member.types.add(self.type_member)

        invoice = Invoice.objects.create(
            member=member,
            amount=Decimal("120.00"),
            pdf=b"%PDF-1.4 test",
        )

        email = InvoiceTool.create_email(invoice, reminder=False)
        self.assertEqual(email.to, ["parent1@example.com", "parent2@example.com"])
        self.assertIn("Factuur contributie", email.subject)
        self.assertNotIn("Herinnering:", email.subject)
        self.assertEqual(len(email.attachments), 1)

        # Test reminder subject
        reminder_email = InvoiceTool.create_email(invoice, reminder=True)
        self.assertIn("Herinnering: Factuur contributie", reminder_email.subject)

    def test_create_email_no_parents_email(self):
        member = self.create_member(
            email_address="child@example.com",
            email_ouders="",
        )
        member.types.add(self.type_member)

        invoice = Invoice.objects.create(
            member=member,
            amount=Decimal("120.00"),
            pdf=b"%PDF-1.4 test",
        )

        email = InvoiceTool.create_email(invoice)
        self.assertEqual(email.to, ["child@example.com"])

    def test_create_email_senior_recipient(self):
        member = self.create_member(
            email_address="senior@example.com",
            email_ouders="parents@example.com",
        )
        member.types.add(self.type_senior)

        invoice = Invoice.objects.create(
            member=member,
            amount=Decimal("90.00"),
            pdf=b"%PDF-1.4 test",
        )

        email = InvoiceTool.create_email(invoice)
        self.assertIn("parents@example.com", email.to)
        self.assertIn("senior@example.com", email.to)

    @patch("LedenAdministratie.invoice.InvoiceTool.render_invoice")
    def test_create_invoice(self, mock_render):
        mock_render.return_value = b"%PDF-mock"
        member = self.create_member()
        lines = [
            InvoiceLine(count=1, amount=Decimal("120.00"), description="Contributie")
        ]

        InvoiceTool.create_invoice(
            invoice_type=InvoiceType.STANDARD,
            member=member,
            lines=lines,
            creator="admin_user",
        )

        invoice = Invoice.objects.filter(member=member).first()
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice.amount, Decimal("120.00"))
        self.assertEqual(invoice.username, "admin_user")
        self.assertEqual(invoice.pdf, b"%PDF-mock")
        mock_render.assert_called_once()
