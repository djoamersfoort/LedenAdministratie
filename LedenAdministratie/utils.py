from typing import Optional

from django.core.mail import EmailMessage
from django.http.request import HttpRequest
from oauth2_provider.models import AccessToken

from LedenAdministratie.models import Setting


class Utils:
    # Send and e-mail, and log it in the email history table
    @staticmethod
    def send_email(message: EmailMessage) -> bool:
        try:
            count = message.send(fail_silently=False)
        except Exception as ex:
            print("Fout bij versturen van e-mail: {0}".format(str(ex)))
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
    def get_access_token(request: HttpRequest) -> Optional[AccessToken]:
        token = request.GET.get("access_token", "").strip()
        if token == "":
            parts = request.headers.get("authorization", "").split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]

        if token == "":
            return None

        try:
            token = AccessToken.objects.get(token=token)
        except AccessToken.DoesNotExist:
            return None
        return token
