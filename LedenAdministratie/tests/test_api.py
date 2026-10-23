import hashlib
import hmac
import io
from datetime import date, timedelta
from PIL import Image

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import AsyncClient, TestCase, override_settings
from django.utils import timezone
from oauth2_provider.models import get_access_token_model, get_application_model

from LedenAdministratie.models import Member, MemberType, Stripcard

User = get_user_model()
Application = get_application_model()
AccessToken = get_access_token_model()

ALLOWED_CLIENT_ID = (
    settings.SMOELENBOEK_API_ALLOWED_CLIENTS[0]
    if getattr(settings, "SMOELENBOEK_API_ALLOWED_CLIENTS", None)
    else "allowed_test_client_id"
)
FAST_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@override_settings(
    PASSWORD_HASHERS=FAST_HASHERS,
    SMOELENBOEK_API_ALLOWED_CLIENTS=[ALLOWED_CLIENT_ID],
)
class ApiTestCaseBase(TestCase):
    def setUp(self):
        self.type_member = MemberType.objects.create(slug="member", display_name="Lid")
        self.type_senior = MemberType.objects.create(
            slug="senior", display_name="Senior Lid"
        )

        self.app_user = User.objects.create_user(
            username="app_owner@example.com",
            email="app_owner@example.com",
            password="password",
        )
        self.allowed_app = Application.objects.create(
            name="Allowed App",
            client_id=ALLOWED_CLIENT_ID,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
            user=self.app_user,
        )
        self.disallowed_app = Application.objects.create(
            name="Disallowed App",
            client_id="disallowed_client_id_12345",
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
            user=self.app_user,
        )

        self.member = self.create_member(
            first_name="Jan",
            last_name="Jansen",
            email_address="jan.jansen@example.com",
            gebdat=date(2005, 5, 15),
            straat="Hoofdstraat 10",
            postcode="1234 AB",
            woonplaats="Amersfoort",
            telnr="0611223344",
            telnr_ouders="0655667788",
            email_ouders="ouders.jansen@example.com",
            aanmeld_datum=date(2020, 1, 1),
            days=1,
        )
        self.member.types.add(self.type_member)

    def create_member(self, **kwargs):
        defaults = {
            "first_name": "Voornaam",
            "last_name": "Achternaam",
            "gebdat": date(2006, 1, 1),
            "geslacht": "m",
            "email_address": "user@example.com",
            "straat": "Straat 1",
            "postcode": "1234 AB",
            "woonplaats": "Amersfoort",
            "telnr": "0600000000",
            "telnr_ouders": "0611111111",
            "email_ouders": "parents@example.com",
            "aanmeld_datum": date(2020, 1, 1),
            "days": 1,
        }
        defaults.update(kwargs)
        return Member.objects.create(**defaults)

    def create_token(self, app, user=None, scopes="user/basic", token_str="test_token"):
        return AccessToken.objects.create(
            user=user or self.app_user,
            application=app,
            token=token_str,
            expires=timezone.now() + timedelta(days=1),
            scope=scopes,
        )


class SmoelenboekApiTests(ApiTestCaseBase):
    def test_smoelenboek_unauthorized_no_token(self):
        response = self.client.get("/api/v1/smoelenboek/")
        self.assertEqual(response.status_code, 403)

    def test_smoelenboek_disallowed_client(self):
        token = self.create_token(self.disallowed_app, token_str="disallowed_tok")
        response = self.client.get(
            "/api/v1/smoelenboek/", HTTP_AUTHORIZATION=f"Bearer {token.token}"
        )
        self.assertEqual(response.status_code, 403)

    def test_smoelenboek_allowed_client_success(self):
        token = self.create_token(self.allowed_app, token_str="allowed_tok")
        response = self.client.get(
            "/api/v1/smoelenboek/", HTTP_AUTHORIZATION=f"Bearer {token.token}"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

        member_data = data[0]
        self.assertEqual(member_data["id"], self.member.id)
        self.assertEqual(member_data["first_name"], "Jan")
        self.assertEqual(member_data["last_name"], "Jansen")
        self.assertEqual(member_data["user_id"], f"idp-{self.member.user.pk}")
        self.assertEqual(member_data["types"], "member")
        self.assertIn("signature=", member_data["photo"])

    def test_smoelenboek_excludes_inactive_members(self):
        self.create_member(
            first_name="Oud",
            last_name="Lid",
            email_address="oud@example.com",
            afmeld_datum=date.today() - timedelta(days=1),
        )
        token = self.create_token(self.allowed_app, token_str="allowed_tok")
        response = self.client.get(
            "/api/v1/smoelenboek/", HTTP_AUTHORIZATION=f"Bearer {token.token}"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.member.id)

    def test_smoelenboek_large_param(self):
        token = self.create_token(self.allowed_app, token_str="allowed_tok")
        response = self.client.get(
            "/api/v1/smoelenboek/?large=1", HTTP_AUTHORIZATION=f"Bearer {token.token}"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("large=1", data[0]["photo"])


class SmoelenboekUserApiTests(ApiTestCaseBase):
    def test_user_unauthorized_no_token(self):
        response = self.client.get(f"/api/v1/smoelenboek/{self.member.id}/")
        self.assertEqual(response.status_code, 403)

    def test_user_disallowed_client(self):
        token = self.create_token(self.disallowed_app, token_str="disallowed_tok")
        response = self.client.get(
            f"/api/v1/smoelenboek/{self.member.id}/",
            HTTP_AUTHORIZATION=f"Bearer {token.token}",
        )
        self.assertEqual(response.status_code, 403)

    def test_user_not_found(self):
        token = self.create_token(self.allowed_app, token_str="allowed_tok")
        response = self.client.get(
            "/api/v1/smoelenboek/99999/",
            HTTP_AUTHORIZATION=f"Bearer {token.token}",
        )
        self.assertEqual(response.status_code, 404)

    def test_user_success(self):
        token = self.create_token(self.allowed_app, token_str="allowed_tok")
        response = self.client.get(
            f"/api/v1/smoelenboek/{self.member.id}/",
            HTTP_AUTHORIZATION=f"Bearer {token.token}",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], self.member.id)
        self.assertEqual(data["first_name"], "Jan")
        self.assertEqual(data["last_name"], "Jansen")
        self.assertEqual(data["types"], "member")
        self.assertIn("signature=", data["photo"])


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class SmoelenboekSignedApiTests(TestCase):
    def setUp(self):
        self.async_client = AsyncClient()
        self.member = Member.objects.create(
            first_name="Photo",
            last_name="Tester",
            gebdat=date(2005, 5, 15),
            geslacht="m",
            email_address="photo@example.com",
            straat="Straat 1",
            postcode="1234 AB",
            woonplaats="Amersfoort",
            telnr_ouders="0612345678",
            email_ouders="parents@example.com",
            aanmeld_datum=date(2020, 1, 1),
        )

    def generate_signed_path(self, query="large=0", expiry_delta_hours=28):
        expiry = int(
            (timezone.now() + timezone.timedelta(hours=expiry_delta_hours)).timestamp()
        )
        base_path = f"/api/v1/smoelenboek/{self.member.id}/{expiry}/?{query}"
        # Build url signature matching request.build_absolute_uri()
        full_url = f"http://testserver{base_path}"
        signature = hmac.new(
            settings.SECRET_KEY.encode(), full_url.encode(), hashlib.sha256
        ).hexdigest()
        return f"{base_path}&signature={signature}", expiry

    async def test_signed_photo_invalid_signature(self):
        expiry = int((timezone.now() + timezone.timedelta(hours=1)).timestamp())
        url = f"/api/v1/smoelenboek/{self.member.id}/{expiry}/?large=0&signature=invalid_signature"
        response = await self.async_client.get(url)
        self.assertEqual(response.status_code, 403)

    async def test_signed_photo_expired(self):
        url, _ = self.generate_signed_path(expiry_delta_hours=-2)
        response = await self.async_client.get(url)
        self.assertEqual(response.status_code, 403)

    async def test_signed_photo_fallback_placeholder_when_no_photo(self):
        url, _ = self.generate_signed_path()
        response = await self.async_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Content-Type"), "image/png")
        self.assertTrue(len(response.content) > 0)

    async def test_signed_photo_with_custom_image(self):
        # Create small test image
        img = Image.new("RGB", (50, 50), color="green")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        self.member.foto = buf.getvalue()
        self.member.thumbnail = buf.getvalue()
        await self.member.asave()

        url, _ = self.generate_signed_path(query="large=1")
        response = await self.async_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Content-Type"), "image/png")
        self.assertEqual(response.content, buf.getvalue())


class UserDetailsApiTests(ApiTestCaseBase):
    def test_user_details_no_token(self):
        response = self.client.get("/api/v1/member/details")
        self.assertEqual(response.status_code, 403)

    def test_user_details_user_without_linked_member(self):
        token = self.create_token(
            self.allowed_app,
            user=self.app_user,
            scopes="user/basic",
            token_str="no_member_tok",
        )
        response = self.client.get(
            "/api/v1/member/details", HTTP_AUTHORIZATION=f"Bearer {token.token}"
        )
        self.assertEqual(response.status_code, 403)

    def test_user_details_basic_scope(self):
        token = self.create_token(
            self.allowed_app,
            user=self.member.user,
            scopes="user/basic",
            token_str="basic_tok",
        )
        response = self.client.get(
            "/api/v1/member/details", HTTP_AUTHORIZATION=f"Bearer {token.token}"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["id"], str(self.member.user.id))
        self.assertEqual(data["username"], self.member.user.username)
        self.assertEqual(data["memberStatus"], True)
        self.assertEqual(data["accountType"], "lid")
        self.assertEqual(data["accountTypes"], ["member"])
        self.assertEqual(data["backendID"], str(self.member.id))
        self.assertEqual(data["days"], 1)

        # Scopes not included
        self.assertNotIn("email", data)
        self.assertNotIn("emailParents", data)
        self.assertNotIn("fullName", data)
        self.assertNotIn("dateOfBirth", data)
        self.assertNotIn("address", data)
        self.assertNotIn("phone", data)

    def test_user_details_stripcard_in_basic_scope(self):
        Stripcard.objects.create(
            member=self.member,
            issue_date=date.today(),
            issued_by="Admin",
            count=10,
            used=3,
            expiration_date=date(2028, 12, 31),
        )
        token = self.create_token(
            self.allowed_app,
            user=self.member.user,
            scopes="user/basic",
            token_str="strip_tok",
        )
        response = self.client.get(
            "/api/v1/member/details", HTTP_AUTHORIZATION=f"Bearer {token.token}"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["stripcard_count"], 10)
        self.assertEqual(data["stripcard_used"], 3)
        self.assertEqual(data["stripcard_expires"], "2028-12-31")

    def test_user_details_all_scopes(self):
        all_scopes = (
            "user/basic user/email user/email-parents user/names "
            "user/date-of-birth user/address user/telephone"
        )
        token = self.create_token(
            self.allowed_app,
            user=self.member.user,
            scopes=all_scopes,
            token_str="all_scopes_tok",
        )
        response = self.client.get(
            "/api/v1/member/details", HTTP_AUTHORIZATION=f"Bearer {token.token}"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # basic
        self.assertEqual(data["username"], "jan.jansen@example.com")
        # email
        self.assertEqual(data["email"], "jan.jansen@example.com")
        # email parents
        self.assertEqual(data["emailParents"], "ouders.jansen@example.com")
        # names
        self.assertEqual(data["fullName"], "Jan Jansen")
        self.assertEqual(data["firstName"], "Jan")
        self.assertEqual(data["middleName"], "")
        self.assertEqual(data["lastName"], "Jansen")
        # dob
        self.assertEqual(data["dateOfBirth"], "2005-05-15")
        self.assertEqual(data["age"], self.member.age)
        # address
        self.assertEqual(data["address"], "Hoofdstraat 10")
        self.assertEqual(data["zip"], "1234 AB")
        self.assertEqual(data["city"], "Amersfoort")
        # telephone
        self.assertEqual(data["phone"], "0611223344")

    def test_user_details_partial_scopes(self):
        token = self.create_token(
            self.allowed_app,
            user=self.member.user,
            scopes="user/basic user/email user/names",
            token_str="partial_scopes_tok",
        )
        response = self.client.get(
            "/api/v1/member/details", HTTP_AUTHORIZATION=f"Bearer {token.token}"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("username", data)
        self.assertIn("email", data)
        self.assertIn("fullName", data)
        self.assertNotIn("address", data)
        self.assertNotIn("phone", data)
        self.assertNotIn("dateOfBirth", data)
        self.assertNotIn("emailParents", data)
