from unittest.mock import MagicMock
from django.core.mail import EmailMessage
from django.test import RequestFactory, TestCase
from django.urls import reverse

from LedenAdministratie.models import Setting
from LedenAdministratie.utils import Utils


class UtilsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_setting_exists(self):
        Setting.objects.create(name="test_key", value="test_value")
        self.assertEqual(Utils.get_setting("test_key"), "test_value")

    def test_get_setting_does_not_exist(self):
        self.assertEqual(Utils.get_setting("non_existent_key"), "")

    def test_get_safe_return_url_valid_referer(self):
        request = self.factory.get(
            "/some/path/", HTTP_REFERER="http://testserver/invoice/search/"
        )
        self.assertEqual(Utils.get_safe_return_url(request), "/invoice/search/")

    def test_get_safe_return_url_external_referer_rejected(self):
        request = self.factory.get(
            "/some/path/", HTTP_REFERER="https://evil.com/invoice/search/"
        )
        self.assertEqual(Utils.get_safe_return_url(request), reverse("members"))

    def test_get_safe_return_url_no_referer(self):
        request = self.factory.get("/some/path/")
        self.assertEqual(Utils.get_safe_return_url(request), reverse("members"))

    def test_get_safe_return_url_empty_referer(self):
        request = self.factory.get("/some/path/", HTTP_REFERER="")
        self.assertEqual(Utils.get_safe_return_url(request), reverse("members"))

    def test_get_safe_return_url_rejects_scheme_relative_url(self):
        request = self.factory.get(
            "/some/path/", HTTP_REFERER="//attacker.com/malicious"
        )
        self.assertEqual(Utils.get_safe_return_url(request), reverse("members"))

    def test_get_safe_return_url_rejects_double_slash_path(self):
        request = self.factory.get(
            "/some/path/", HTTP_REFERER="http://testserver//attacker.com/malicious"
        )
        self.assertEqual(Utils.get_safe_return_url(request), reverse("members"))

    def test_get_signed_url(self):
        request = self.factory.get("/api/v1/smoelenboek/")
        signed_url = Utils.get_signed_url(request, "1/1234567890/?large=0")
        self.assertIn("1/1234567890/?large=0", signed_url)
        self.assertIn("&signature=", signed_url)

    def test_send_email_success(self):
        message = MagicMock(spec=EmailMessage)
        message.send.return_value = 1
        self.assertTrue(Utils.send_email(message))
        message.send.assert_called_once_with(fail_silently=False)

    def test_send_email_failure_returns_zero(self):
        message = MagicMock(spec=EmailMessage)
        message.send.return_value = 0
        self.assertFalse(Utils.send_email(message))

    def test_send_email_exception(self):
        message = MagicMock(spec=EmailMessage)
        message.send.side_effect = Exception("SMTP error")
        self.assertFalse(Utils.send_email(message))
