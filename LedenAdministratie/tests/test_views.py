from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from LedenAdministratie.mixins import PermissionRequiredMixin
from LedenAdministratie.models import Invoice, Member, MemberType, Note, Stripcard
from LedenAdministratie.views import (
    InvoiceDeleteView,
    InvoicePayFullView,
    LoggedInView,
    MemberDeleteNoteView,
    Profile,
    StripcardDeleteView,
)

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

    def test_member_delete_note_view_get_method_not_allowed(self):
        note = Note.objects.create(
            member=self.member, text="Test Note", username="admin"
        )
        perm = Permission.objects.get(codename="delete_note")
        self.member.user.user_permissions.add(perm)

        request = self.factory.get(f"/member/delnote/{note.pk}")
        request.user = self.member.user
        request.user.is_verified = lambda: True

        response = MemberDeleteNoteView.as_view()(request, pk=note.pk)
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Note.objects.filter(pk=note.pk).exists())

    def test_member_delete_note_view_post_success(self):
        note = Note.objects.create(
            member=self.member, text="Test Note", username="admin"
        )
        perm = Permission.objects.get(codename="delete_note")
        self.member.user.user_permissions.add(perm)

        request = self.factory.post(f"/member/delnote/{note.pk}")
        request.user = self.member.user
        request.user.is_verified = lambda: True

        response = MemberDeleteNoteView.as_view()(request, pk=note.pk)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Note.objects.filter(pk=note.pk).exists())

    def test_invoice_delete_view_get_method_not_allowed(self):
        invoice = Invoice.objects.create(
            member=self.member,
            amount=Decimal("20.00"),
            username="admin",
        )
        perm = Permission.objects.get(codename="delete_invoice")
        self.member.user.user_permissions.add(perm)

        request = self.factory.get(f"/invoice/delete/{invoice.pk}")
        request.user = self.member.user
        request.user.is_verified = lambda: True

        response = InvoiceDeleteView.as_view()(request, pk=invoice.pk)
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Invoice.objects.filter(pk=invoice.pk).exists())

    def test_invoice_delete_view_post_success(self):
        invoice = Invoice.objects.create(
            member=self.member,
            amount=Decimal("20.00"),
            username="admin",
        )
        perm = Permission.objects.get(codename="delete_invoice")
        self.member.user.user_permissions.add(perm)

        request = self.factory.post(f"/invoice/delete/{invoice.pk}")
        request.user = self.member.user
        request.user.is_verified = lambda: True

        response = InvoiceDeleteView.as_view()(request, pk=invoice.pk)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Invoice.objects.filter(pk=invoice.pk).exists())

    def test_invoice_pay_full_view_get_method_not_allowed(self):
        invoice = Invoice.objects.create(
            member=self.member,
            amount=Decimal("20.00"),
            amount_payed=Decimal("0.00"),
            username="admin",
        )
        perm = Permission.objects.get(codename="view_invoice")
        self.member.user.user_permissions.add(perm)

        request = self.factory.get(f"/invoice/pay_full/{invoice.pk}")
        request.user = self.member.user
        request.user.is_verified = lambda: True

        response = InvoicePayFullView.as_view()(request, pk=invoice.pk)
        self.assertEqual(response.status_code, 405)
        invoice.refresh_from_db()
        self.assertEqual(invoice.amount_payed, Decimal("0.00"))

    def test_invoice_pay_full_view_post_success(self):
        invoice = Invoice.objects.create(
            member=self.member,
            amount=Decimal("20.00"),
            amount_payed=Decimal("0.00"),
            username="admin",
        )
        perm = Permission.objects.get(codename="view_invoice")
        self.member.user.user_permissions.add(perm)

        request = self.factory.post(f"/invoice/pay_full/{invoice.pk}")
        request.user = self.member.user
        request.user.is_verified = lambda: True

        response = InvoicePayFullView.as_view()(request, pk=invoice.pk)
        self.assertEqual(response.status_code, 302)
        invoice.refresh_from_db()
        self.assertEqual(invoice.amount_payed, Decimal("20.00"))

    def test_stripcard_delete_view_get_method_not_allowed(self):
        stripcard = Stripcard.objects.create(
            member=self.member,
            issue_date=date(2023, 1, 1),
            issued_by="admin",
            count=10,
        )
        perm = Permission.objects.get(codename="delete_stripcard")
        self.member.user.user_permissions.add(perm)

        request = self.factory.get(f"/stripcard/delete/{stripcard.pk}")
        request.user = self.member.user
        request.user.is_verified = lambda: True

        response = StripcardDeleteView.as_view()(request, pk=stripcard.pk)
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Stripcard.objects.filter(pk=stripcard.pk).exists())

    def test_stripcard_delete_view_post_success(self):
        stripcard = Stripcard.objects.create(
            member=self.member,
            issue_date=date(2023, 1, 1),
            issued_by="admin",
            count=10,
        )
        perm = Permission.objects.get(codename="delete_stripcard")
        self.member.user.user_permissions.add(perm)

        request = self.factory.post(f"/stripcard/delete/{stripcard.pk}")
        request.user = self.member.user
        request.user.is_verified = lambda: True

        response = StripcardDeleteView.as_view()(request, pk=stripcard.pk)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Stripcard.objects.filter(pk=stripcard.pk).exists())
