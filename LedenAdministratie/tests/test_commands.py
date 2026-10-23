from datetime import date, timedelta
from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import TestCase, override_settings

from LedenAdministratie.models import Member, MemberType, Note, Stripcard

FAST_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class SyncStripcardsCommandTests(TestCase):
    def setUp(self):
        self.type_member = MemberType.objects.create(slug="member", display_name="Lid")
        self.member = Member.objects.create(
            first_name="Sync",
            last_name="Member",
            gebdat=date(2005, 1, 1),
            geslacht="m",
            email_address="sync@example.com",
            straat="Straat 1",
            postcode="1234 AB",
            woonplaats="Amersfoort",
            telnr_ouders="0612345678",
            email_ouders="parents@example.com",
            aanmeld_datum=date(2020, 1, 1),
        )

    @patch("requests.get")
    def test_sync_stripcards_updates_count(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"count": 4}
        mock_get.return_value = mock_response

        card = Stripcard.objects.create(
            member=self.member,
            issue_date=date(2023, 1, 1),
            issued_by="Admin",
            count=10,
            used=1,
            expiration_date=date.today() + timedelta(days=365),
        )

        out = StringIO()
        call_command("sync_stripcards", stdout=out)

        card.refresh_from_db()
        self.assertEqual(card.used, 4)
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_sync_stripcards_full_card_is_skipped(self, mock_get):
        card = Stripcard.objects.create(
            member=self.member,
            issue_date=date(2023, 1, 1),
            issued_by="Admin",
            count=10,
            used=10,
            expiration_date=date.today() + timedelta(days=365),
        )

        out = StringIO()
        call_command("sync_stripcards", stdout=out)

        mock_get.assert_not_called()
        card.refresh_from_db()
        self.assertEqual(card.used, 10)

    def test_sync_stripcards_expired_card_is_deleted_with_note(self):
        card = Stripcard.objects.create(
            member=self.member,
            issue_date=date(2020, 1, 1),
            issued_by="Admin",
            count=10,
            used=3,
            expiration_date=date.today() - timedelta(days=1),
        )

        out = StringIO()
        call_command("sync_stripcards", stdout=out)

        self.assertFalse(Stripcard.objects.filter(pk=card.pk).exists())
        note = Note.objects.filter(member=self.member).first()
        self.assertIsNotNone(note)
        self.assertIn("Deleting expired stripcard", note.text)
        self.assertTrue(note.done)

    @patch("requests.get")
    def test_sync_stripcards_api_error_handled_gracefully(self, mock_get):
        mock_get.side_effect = ConnectionError("Connection refused")

        card = Stripcard.objects.create(
            member=self.member,
            issue_date=date(2023, 1, 1),
            issued_by="Admin",
            count=10,
            used=1,
            expiration_date=date.today() + timedelta(days=365),
        )

        out = StringIO()
        call_command("sync_stripcards", stdout=out)

        card.refresh_from_db()
        self.assertEqual(card.used, 1)  # Unchanged
