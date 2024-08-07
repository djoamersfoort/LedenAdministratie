import requests
from django.core.management.base import BaseCommand
from django.utils import timezone

from LedenAdministratie.models import Stripcard


class Command(BaseCommand):
    def handle(self, *args, **options):
        cards_to_delete: list[Stripcard] = []
        # Sync stripcard 'used' column with aanmelden app
        for stripcard in Stripcard.objects.all():
            if stripcard.count == stripcard.used:
                # This card is full -> skip
                continue

            if timezone.now().date() > stripcard.expiration_date:
                # This card has expired -> delete
                cards_to_delete.append(stripcard)
                continue

            userid = f"idp-{stripcard.member.user.pk}"
            issue_date = stripcard.issue_date
            url = (
                f"https://aanmelden.djoamersfoort.nl/api/v1/present_since_date/"
                f"{userid}/{issue_date.year}/{issue_date.month}/{issue_date.day}"
            )
            # Get the number of presences since stripcard issue date
            try:
                count = requests.get(url, timeout=20).json()["count"]
            except (IOError, ConnectionError) as ex:
                self.stdout.write(
                    self.style.ERROR(f"Error querying aanmelden service: {ex}")
                )
                continue
            self.stdout.write(self.style.SUCCESS(f"Calling: {url}, Returned {count}"))
            if count > stripcard.count:
                # Stripcard if full -> there should be a new one with free slots
                stripcard.used = stripcard.count
            else:
                stripcard.used = count
            stripcard.save()

        # Remove expired stripcards
        for stripcard in cards_to_delete:
            self.stdout.write(
                self.style.SUCCESS(f"Deleting expired stripcard: {stripcard}")
            )
            stripcard.delete()
