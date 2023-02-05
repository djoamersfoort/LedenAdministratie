import requests
from django.core.management.base import BaseCommand

from LedenAdministratie.models import Stripcard


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Sync stripcard 'used' column with aanmelden app
        for stripcard in Stripcard.objects.all():
            userid = f"idp-{stripcard.member.pk}"
            issue_date = stripcard.issue_date
            url = (
                f"https://aanmelden.djoamersfoort.nl/api/v1/present_since_date/"
                f"{userid}/{issue_date.year}/{issue_date.month}/{issue_date.day}"
            )
            # Get the number of presences since stripcard issue date
            try:
                count = requests.get(url).json()["count"]
            except (IOError, ConnectionError) as ex:
                self.stdout.write(self.style.ERROR(f"Error querying aanmelden service: {ex}"))
                continue
            self.stdout.write(self.style.SUCCESS(f"Calling: {url}, Returned {count}"))
            if count > stripcard.count:
                # Stripcard if full -> there should be a new one with free slots
                stripcard.used = stripcard.count
            else:
                stripcard.used = count
            stripcard.save()
