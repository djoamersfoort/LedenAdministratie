from datetime import date
from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from LedenAdministratie.mixins import PermissionRequiredMixin
from LedenAdministratie.models import Member, MemberType
from LedenAdministratie.views import LoggedInView, Profile

User = get_user_model()
FAST_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class PermissionRequiredMixinTests(TestCase):
    def setUp(self):
        self.mixin = PermissionRequiredMixin()
        self.user = User.objects.create_user(username="testuser", password="password")

    def test_check_user_anonymous(self):
        anon_user = MagicMock()
        anon_user.is_authenticated = False
        self.assertFalse(self.mixin.check_user(anon_user))

    def test_check_user_without_permission(self):
        self.assertFalse(self.mixin.check_user(self.user))

    def test_check_user_with_permission(self):
        perm = Permission.objects.get(codename="view_member")
        self.user.user_permissions.add(perm)
        self.assertTrue(self.mixin.check_user(self.user))

    def test_check_user_inactive(self):
        perm = Permission.objects.get(codename="view_member")
        self.user.user_permissions.add(perm)
        self.user.is_active = False
        self.assertFalse(self.mixin.check_user(self.user))


@override_settings(PASSWORD_HASHERS=FAST_HASHERS)
class ViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.type_member = MemberType.objects.create(slug="member", display_name="Lid")
        self.member = Member.objects.create(
            first_name="View",
            last_name="Tester",
            gebdat=date(2005, 1, 1),
            geslacht="m",
            email_address="viewtester@example.com",
            straat="Straat 1",
            postcode="1234 AB",
            woonplaats="Amersfoort",
            telnr_ouders="0612345678",
            email_ouders="parents@example.com",
            aanmeld_datum=date(2020, 1, 1),
        )

    def test_logged_in_view_unverified_or_no_perm_redirects_to_profile(self):
        request = self.factory.get("/logged_in/")
        request.user = self.member.user
        # Mock is_verified
        request.user.is_verified = lambda: False

        response = LoggedInView.as_view()(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("profile"))

    def test_logged_in_view_verified_with_perm_redirects_to_members(self):
        perm = Permission.objects.get(codename="view_member")
        self.member.user.user_permissions.add(perm)

        request = self.factory.get("/logged_in/")
        request.user = self.member.user
        request.user.is_verified = lambda: True

        response = LoggedInView.as_view()(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("members"))

    def test_profile_post_forbidden(self):
        request = self.factory.post("/profile/")
        request.user = self.member.user
        response = Profile.as_view()(request)
        self.assertEqual(response.status_code, 403)
