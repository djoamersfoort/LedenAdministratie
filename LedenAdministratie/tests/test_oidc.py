from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from LedenAdministratie.models import Member, MemberType, Stripcard
from LedenAdministratie.oidc import DJOOAuth2Validator

User = get_user_model()
FAST_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class DJOOAuth2ValidatorTests(TestCase):
    def setUp(self):
        self.validator = DJOOAuth2Validator()
        self.type_member = MemberType.objects.create(slug="member", display_name="Lid")
        self.member = Member.objects.create(
            first_name="Alice",
            last_name="Tester",
            gebdat=date(2004, 3, 10),
            geslacht="v",
            email_address="alice@example.com",
            straat="Straat 2",
            postcode="2345 CD",
            woonplaats="Amersfoort",
            telnr_ouders="0611112222",
            email_ouders="parents@example.com",
            aanmeld_datum=date(2020, 1, 1),
            days=2,
        )
        self.member.types.add(self.type_member)

    def test_additional_claims_basic_and_profile(self):
        request = MagicMock()
        request.user = self.member.user

        claims = self.validator.get_additional_claims()
        self.assertEqual(claims["given_name"](request), "Alice")
        self.assertEqual(claims["family_name"](request), "Tester")
        self.assertEqual(claims["email"](request), "alice@example.com")
        self.assertEqual(claims["aanmelden"](request), True)
        self.assertEqual(claims["media"](request), True)
        self.assertEqual(claims["corvee"](request), True)
        self.assertEqual(claims["account_type"](request), "lid")
        self.assertEqual(claims["days"](request), 2)
        self.assertIsNone(claims["stripcard"](request))

    def test_additional_claims_stripcard(self):
        Stripcard.objects.create(
            member=self.member,
            issue_date=date.today(),
            issued_by="admin",
            count=10,
            used=4,
            expiration_date=date(2025, 12, 31),
        )
        request = MagicMock()
        request.user = self.member.user

        claims = self.validator.get_additional_claims()
        stripcard_claim = claims["stripcard"](request)
        self.assertIsNotNone(stripcard_claim)
        self.assertEqual(stripcard_claim["count"], 10)
        self.assertEqual(stripcard_claim["used"], 4)
        self.assertEqual(stripcard_claim["expires"], date(2025, 12, 31))

    @patch("oauth2_provider.oauth2_validators.OAuth2Validator.validate_user")
    def test_validate_user_active_member(self, mock_super_validate):
        mock_super_validate.return_value = True
        request = MagicMock()
        request.user = self.member.user

        result = self.validator.validate_user(
            username=self.member.user.username,
            password="password",
            client=MagicMock(),
            request=request,
        )
        self.assertTrue(result)

    @patch("oauth2_provider.oauth2_validators.OAuth2Validator.validate_user")
    def test_validate_user_inactive_member(self, mock_super_validate):
        mock_super_validate.return_value = True
        self.member.afmeld_datum = date.today() - timedelta(days=1)
        self.member.save()

        request = MagicMock()
        request.user = self.member.user

        result = self.validator.validate_user(
            username=self.member.user.username,
            password="password",
            client=MagicMock(),
            request=request,
        )
        self.assertFalse(result)

    @patch("oauth2_provider.oauth2_validators.OAuth2Validator.validate_user")
    def test_validate_user_super_fails(self, mock_super_validate):
        mock_super_validate.return_value = False
        request = MagicMock()
        request.user = self.member.user

        result = self.validator.validate_user(
            username=self.member.user.username,
            password="wrong_password",
            client=MagicMock(),
            request=request,
        )
        self.assertFalse(result)
