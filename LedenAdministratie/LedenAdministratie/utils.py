from django.core.mail import EmailMessage
from django.utils import timezone
from .models import Email, Setting


class Utils:
    # Send and e-mail, and log it in the email history table
    @staticmethod
    def send_email(message, username, member):
        log = Email()
        log.member = member
        log.subject = message.subject
        log.recipients = ",".join(message.recipients())
        log.sent_by = username
        log.sent = timezone.now()
        count = 0
        try:
            count = message.send(fail_silently=False)
            if count == 1:
                log.status = 'OK'
            else:
                log.status = 'Fout bij versturen!'
        except Exception as e:
            log.status = "Fout bij versturen: {0}".format(str(e))

        log.save_base()
        return count == 1

    @staticmethod
    def get_setting(name):
        try:
            setting = Setting.objects.get(name=name)
        except Setting.DoesNotExist:
            return ""
        return setting.value
