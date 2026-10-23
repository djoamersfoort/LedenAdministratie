import io
from datetime import date, timedelta
from decimal import Decimal

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from LedenAdministratie.models import (
    Member,
    MemberType,
    Note,
    Invoice,
    Setting,
    Stripcard,
)

User = get_user_model()
FAST_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class MemberModelTests(TestCase):
    def setUp(self):
        self.type_member = MemberType.objects.create(slug="member", display_name="Lid")
        self.type_senior = MemberType.objects.create(
            slug="senior", display_name="Senior Lid"
        )
        self.type_bestuur = MemberType.objects.create(
            slug="bestuur", display_name="Bestuurslid"
        )
        self.type_begeleider = MemberType.objects.create(
            slug="begeleider", display_name="Begeleider"
        )
        self.type_ondersteuning = MemberType.objects.create(
            slug="ondersteuning", display_name="Ondersteuner"
        )
        self.type_aspirant = MemberType.objects.create(
            slug="aspirant", display_name="Aspirant"
        )
        self.type_stripcard = MemberType.objects.create(
            slug="strippenkaart", display_name="Strippenkaart"
        )

    def create_sample_member(self, **kwargs):
        defaults = {
            "first_name": "Jan",
            "last_name": "Jansen",
            "gebdat": date(2005, 5, 15),
            "geslacht": "m",
            "email_address": "jan.jansen@example.com",
            "straat": "Kerkstraat 1",
            "postcode": "1234 AB",
            "woonplaats": "Amersfoort",
            "telnr": "0612345678",
            "telnr_ouders": "0687654321",
            "email_ouders": "ouders.jansen@example.com",
            "aanmeld_datum": date(2020, 1, 1),
            "days": 1,
        }
        defaults.update(kwargs)
        return Member.objects.create(**defaults)

    def test_member_type_str(self):
        self.assertEqual(str(self.type_member), "Lid")

    def test_member_creation_creates_linked_user(self):
        member = self.create_sample_member()
        self.assertIsNotNone(member.user)
        self.assertEqual(member.user.username, "jan.jansen@example.com")
        self.assertEqual(member.user.email, "jan.jansen@example.com")
        self.assertEqual(member.user.first_name, "Jan")
        self.assertEqual(member.user.last_name, "Jansen")
        self.assertTrue(member.user.is_active)
        self.assertTrue(member.user.has_usable_password())

    def test_member_update_syncs_user(self):
        member = self.create_sample_member()
        member.first_name = "Piet"
        member.last_name = "Pietersen"
        member.email_address = "piet.pietersen@example.com"
        member.save()

        user = User.objects.get(pk=member.user.pk)
        self.assertEqual(user.first_name, "Piet")
        self.assertEqual(user.last_name, "Pietersen")
        self.assertEqual(user.username, "piet.pietersen@example.com")
        self.assertEqual(user.email, "piet.pietersen@example.com")

    def test_member_full_name_and_str(self):
        member = self.create_sample_member(first_name="Klaas", last_name="de Vries")
        self.assertEqual(member.full_name, "Klaas de Vries")
        self.assertEqual(str(member), "Klaas de Vries")

    def test_member_age_calculation(self):
        # pylint: disable=protected-access
        member = self.create_sample_member(gebdat=date(2000, 6, 15))
        # Test calculation on specific dates
        self.assertEqual(member._calculate_age(on_date=date(2020, 6, 14)), 19)
        self.assertEqual(member._calculate_age(on_date=date(2020, 6, 15)), 20)
        self.assertEqual(member._calculate_age(on_date=date(2020, 6, 16)), 20)
        # Property calculation against today
        expected_age = member._calculate_age(on_date=date.today())
        self.assertEqual(member.age, expected_age)

    def test_member_is_active(self):
        member_no_afmeld = self.create_sample_member(afmeld_datum=None)
        self.assertTrue(member_no_afmeld.is_active())

        member_future = self.create_sample_member(
            email_address="future@example.com",
            afmeld_datum=date.today() + timedelta(days=30),
        )
        self.assertTrue(member_future.is_active())

        member_past = self.create_sample_member(
            email_address="past@example.com",
            afmeld_datum=date.today() - timedelta(days=1),
        )
        self.assertFalse(member_past.is_active())

    def test_member_types_and_roles(self):
        member = self.create_sample_member()
        member.types.add(self.type_member, self.type_bestuur)

        self.assertEqual(member.get_types_display(), "Lid,Bestuurslid")
        self.assertEqual(member.idp_types(), "lid,bestuur")
        self.assertTrue(member.is_standard())
        self.assertTrue(member.is_bestuur())
        self.assertFalse(member.is_begeleider())
        self.assertFalse(member.is_ondersteuner())
        self.assertFalse(member.is_aspirant())
        self.assertFalse(member.is_senior())
        self.assertFalse(member.is_stripcard())

    def test_member_all_roles(self):
        member = self.create_sample_member()
        member.types.add(
            self.type_senior,
            self.type_begeleider,
            self.type_ondersteuning,
            self.type_aspirant,
            self.type_stripcard,
        )
        self.assertTrue(member.is_senior())
        self.assertTrue(member.is_begeleider())
        self.assertTrue(member.is_ondersteuner())
        self.assertTrue(member.is_aspirant())
        self.assertTrue(member.is_stripcard())
        self.assertIn("aspirant_begeleider", member.idp_types())

    def test_thumbnail_generation_from_photo(self):
        # Create a small RGB test image
        img = Image.new("RGB", (200, 300), color="blue")
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG")
        photo_bytes = img_byte_arr.getvalue()

        member = self.create_sample_member(foto=photo_bytes)
        self.assertIsNotNone(member.thumbnail)
        # Check thumbnail can be opened with PIL and has resized dimensions <= (100, 150)
        thumb_img = Image.open(io.BytesIO(member.thumbnail))
        self.assertLessEqual(thumb_img.width, 100)
        self.assertLessEqual(thumb_img.height, 150)

    def test_active_stripcard_property(self):
        member = self.create_sample_member()
        self.assertIsNone(member.active_stripcard)

        # Create a fully used stripcard
        Stripcard.objects.create(
            member=member,
            issue_date=date.today(),
            issued_by="Admin",
            count=10,
            used=10,
        )
        self.assertIsNone(member.active_stripcard)

        # Create an active stripcard with remaining slots
        active_card = Stripcard.objects.create(
            member=member,
            issue_date=date.today(),
            issued_by="Admin",
            count=10,
            used=3,
        )
        self.assertEqual(member.active_stripcard, active_card)


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class InvoiceModelTests(TestCase):
    def setUp(self):
        self.member = Member.objects.create(
            first_name="Test",
            last_name="User",
            gebdat=date(2000, 1, 1),
            geslacht="m",
            email_address="test@example.com",
            straat="Straat 1",
            postcode="1234 AB",
            woonplaats="Plaats",
            telnr_ouders="0612345678",
            email_ouders="parents@example.com",
            aanmeld_datum=date(2020, 1, 1),
        )

    def test_invoice_numbers_and_properties(self):
        invoice = Invoice.objects.create(
            member=self.member,
            amount=Decimal("120.00"),
            amount_payed=Decimal("50.00"),
            username="admin",
        )
        expected_nr = f"F1{self.member.id:04d}-{invoice.id:05d}"
        expected_old_nr = f"F0{self.member.id:04d}-{invoice.id:05d}"
        self.assertEqual(invoice.invoice_number, expected_nr)
        self.assertEqual(invoice.old_invoice_number, expected_old_nr)
        self.assertFalse(invoice.payed)
        self.assertEqual(invoice.amount_unpaid, Decimal("70.00"))

        invoice.amount_payed = Decimal("120.00")
        invoice.save()
        self.assertTrue(invoice.payed)
        self.assertEqual(invoice.amount_unpaid, Decimal("0.00"))

    def test_invoice_str(self):
        invoice = Invoice.objects.create(
            member=self.member,
            amount=Decimal("100.00"),
            amount_payed=Decimal("0.00"),
            username="admin",
        )
        self.assertIn("Door admin voor Test User", str(invoice))
        self.assertIn("100.00", str(invoice))


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class NoteAndSettingAndStripcardModelTests(TestCase):
    def test_note_creation(self):
        member = Member.objects.create(
            first_name="Note",
            last_name="Member",
            gebdat=date(2000, 1, 1),
            geslacht="m",
            email_address="notemember@example.com",
            straat="Straat 1",
            postcode="1234 AB",
            woonplaats="Plaats",
            telnr_ouders="0612345678",
            email_ouders="parents@example.com",
            aanmeld_datum=date(2020, 1, 1),
        )
        note = Note.objects.create(
            member=member,
            username="mentor",
            text="Belangrijke notitie",
            done=False,
        )
        self.assertEqual(note.member, member)
        self.assertEqual(note.text, "Belangrijke notitie")
        self.assertFalse(note.done)

    def test_setting_str(self):
        setting = Setting.objects.create(name="invoice_amount_year", value="150.00")
        self.assertEqual(str(setting), "invoice_amount_year = 150.00")

    def test_stripcard_str(self):
        member = Member.objects.create(
            first_name="Strip",
            last_name="CardHolder",
            gebdat=date(2000, 1, 1),
            geslacht="m",
            email_address="strip@example.com",
            straat="Straat 1",
            postcode="1234 AB",
            woonplaats="Plaats",
            telnr_ouders="0612345678",
            email_ouders="parents@example.com",
            aanmeld_datum=date(2020, 1, 1),
        )
        card = Stripcard.objects.create(
            member=member,
            issue_date=date.today(),
            issued_by="admin",
            count=10,
            used=2,
        )
        self.assertIn(
            "Strippenkaart: Door admin, voor Strip CardHolder, voor 10 keer", str(card)
        )
