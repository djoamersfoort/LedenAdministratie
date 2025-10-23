import hashlib
import hmac
from urllib.parse import urlparse

from django.conf import settings
from django.core.mail import EmailMessage
from django.http.request import HttpRequest
from django.shortcuts import reverse

from LedenAdministratie.models import Setting


class Utils:
    # Send and e-mail, and log it in the email history table
    @staticmethod
    def send_email(message: EmailMessage) -> bool:
        try:
            count = message.send(fail_silently=False)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            print(f"Fout bij versturen van e-mail: {ex}")
            return False
        return count == 1

    @staticmethod
    def get_setting(name: str) -> str:
        try:
            setting = Setting.objects.get(name=name)
        except Setting.DoesNotExist:
            return ""
        return setting.value

    @staticmethod
    def get_safe_return_url(request: HttpRequest) -> str:
        if url := request.META.get("HTTP_REFERER", ""):
            print(f"REFER: {url}")
            path = urlparse(url).path
            if path.startswith("/"):
                return path
        return reverse("members")

    @staticmethod
    def get_signed_url(request: HttpRequest, path: str) -> str:
        url = request.build_absolute_uri(path)
        signature = hmac.new(
            settings.SECRET_KEY.encode(), url.encode(), hashlib.sha256
        ).hexdigest()
        url += f"&signature={signature}"
        return url
