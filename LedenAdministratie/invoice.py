import dataclasses
import os
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML, CSS, default_url_fetcher
from weasyprint.text.fonts import FontConfiguration

from LedenAdministratie.models import Member, Invoice
from LedenAdministratie.utils import Utils


class InvoiceType(Enum):
    STANDARD = "standaard"
    SENIOR = "senior"
    MARCH = "maart"
    SPONSOR = "sponsor"
    STRIPCARD = "strippenkaart"
    TWO_DAYS = "2dagen"
    CUSTOM = "custom"


@dataclasses.dataclass
class InvoiceLine:
    count: int = 0
    amount: Decimal = 0
    description: str = ""

    @property
    def line_total(self):
        return self.count * self.amount


INVOICE_TYPES = (
    (InvoiceType.STANDARD.value, "Standaard factuur voor 1 jaar"),
    (InvoiceType.SENIOR.value, "Senior Lid factuur voor 1 jaar"),
    (InvoiceType.MARCH.value, "Factuur voor lid ingeschreven na 1 maart"),
    (InvoiceType.TWO_DAYS.value, "Factuur voor lid dat beide dagen komt"),
    (InvoiceType.SPONSOR.value, "Sponsor factuur"),
    (InvoiceType.STRIPCARD.value, "Factuur voor lid met strippenkaart"),
    (InvoiceType.CUSTOM.value, "Aangepaste factuur"),
)


class InvoiceTool:
    @staticmethod
    def calculate_grand_total(lines: list[InvoiceLine]):
        grand_total = 0
        for line in lines:
            grand_total += line.count * line.amount
        return grand_total

    @staticmethod
    def invoice_url_fetcher(url: str, timeout: int = 10) -> dict:
        if url.startswith("local:"):
            parts = url.split(":")
            path = parts[1]
            mime_type = parts[2]
            path = os.path.join(settings.BASE_DIR, path)
            file_obj = open(path, "rb")  # pylint: disable=consider-using-with
            return {"file_obj": file_obj, "mime_type": mime_type}
        return default_url_fetcher(url, timeout)

    @staticmethod
    def render_invoice(
        member: Member,
        lines: list[InvoiceLine],
        invoice_number: str,
        invoice_type: InvoiceType,
    ) -> bytes:
        invoice_date = date.today().strftime("%d-%m-%Y")
        due_date = (date.today() + timedelta(days=14)).strftime("%d-%m-%Y")
        extra_text = InvoiceTool.get_extra_text_for_invoice_type(invoice_type)
        title = InvoiceTool.get_title_for_invoice_type(invoice_type)

        grand_total = 0
        valid_lines = []
        for line in lines:
            if line.count != 0:
                grand_total += line.count * line.amount
                valid_lines.append(line)

        font_config = FontConfiguration()
        css = CSS(
            string=render_to_string("invoice/invoice.css"), font_config=font_config
        )
        html = render_to_string(
            "invoice/invoice.html",
            context={
                "lines": valid_lines,
                "extra_text": extra_text,
                "member": member,
                "invoicenr": invoice_number,
                "title": title,
                "date": invoice_date,
                "due_date": due_date,
                "grand_total": grand_total,
            },
        )
        printer = HTML(string=html, url_fetcher=InvoiceTool.invoice_url_fetcher)
        return printer.write_pdf(stylesheets=[css])

    @staticmethod
    def get_title_for_invoice_type(invoice_type: InvoiceType):
        title = "Aan:"
        if invoice_type in [
            InvoiceType.STANDARD,
            InvoiceType.STRIPCARD,
            InvoiceType.TWO_DAYS,
            InvoiceType.MARCH,
        ]:
            title = "Aan de ouders/verzorgers van:"
        return title

    @staticmethod
    def get_extra_text_for_invoice_type(invoice_type: InvoiceType) -> str:
        extra_text = ""
        if invoice_type in [
            InvoiceType.STANDARD,
            InvoiceType.TWO_DAYS,
            InvoiceType.SENIOR,
        ] and date.today() < date(date.today().year, 5, 1):
            extra_text = (
                "Het is mogelijk om in 2 termijnen te betalen\n"
                "De eerste helft van het bedrag graag binnen 14 dagen betalen.\n"
                "Het tweede deel graag uiterlijk 30 april voldoen."
            )
        return extra_text

    @staticmethod
    def get_defaults_for_invoice_type(
        invoice_type: InvoiceType, member: Optional[Member] = None
    ):
        defaults = [
            {
                "description": f"Contributie {date.today().year} DJO Amersfoort",
                "count": 1,
                "amount": Decimal(Utils.get_setting("invoice_amount_year")),
            }
        ]

        if invoice_type == InvoiceType.SENIOR:
            defaults = [
                {
                    "description": f"Contributie senior lid {date.today().year} DJO Amersfoort",
                    "count": 1,
                    "amount": Decimal(Utils.get_setting("invoice_amount_year_senior")),
                }
            ]
        elif invoice_type == InvoiceType.MARCH:
            aanmeld_datum = member.aanmeld_datum if member else date.today()
            defaults = [
                {
                    "description": f"Contributie {date.today().year} DJO Amersfoort",
                    "count": 1,
                    "amount": Decimal(Utils.get_setting("invoice_amount_year")),
                },
                {
                    "description": f"Correctie vanwege inschrijfdatum {aanmeld_datum.strftime('%d-%m-%Y')}",
                    "count": -(aanmeld_datum.month - 1),
                    "amount": Decimal(Utils.get_setting("invoice_amount_month")),
                },
            ]
        elif invoice_type == InvoiceType.STRIPCARD:
            defaults = [
                {
                    "description": f"Strippenkaart {date.today().year} DJO Amersfoort",
                    "count": 10,
                    "amount": Decimal(Utils.get_setting("invoice_amount_day")),
                }
            ]
        elif invoice_type == InvoiceType.SPONSOR:
            defaults = [
                {
                    "description": f"Sponsor {date.today().year} DJO Amersfoort",
                    "count": 1,
                    "amount": Decimal(Utils.get_setting("invoice_amount_sponsor")),
                }
            ]
        elif invoice_type == InvoiceType.TWO_DAYS:
            defaults = [
                {
                    "description": f"Contributie {date.today().year} DJO Amersfoort",
                    "count": 1,
                    "amount": Decimal(Utils.get_setting("invoice_amount_year")),
                },
                {
                    "description": "Toeslag voor deelname op beide dagen",
                    "count": 1,
                    "amount": Decimal(Utils.get_setting("invoice_amount_year")) / 2,
                },
            ]
        elif invoice_type == InvoiceType.CUSTOM:
            defaults = []

        return defaults

    @staticmethod
    def get_members_invoice_type(invoice_type: InvoiceType):
        members = Member.objects.filter(
            types__slug="member", aanmeld_datum__lt=date(date.today().year, 3, 1)
        )
        if invoice_type == InvoiceType.SENIOR:
            members = Member.objects.filter(types__slug="senior")
        elif invoice_type == InvoiceType.SPONSOR:
            members = Member.objects.filter(types__slug="sponsor")
        elif invoice_type == InvoiceType.MARCH:
            members = Member.objects.filter(
                types__slug="member", aanmeld_datum__gt=date(date.today().year, 2, 28)
            )
        elif invoice_type == InvoiceType.STRIPCARD:
            members = Member.objects.filter(types__slug="strippenkaart")
        elif invoice_type == InvoiceType.TWO_DAYS:
            members = Member.objects.filter(types__slug="member", days=2)
        elif invoice_type == InvoiceType.CUSTOM:
            members = Member.objects.all()

        # Only return active members
        members = members.filter(
            Q(afmeld_datum__gt=date.today()) | Q(afmeld_datum=None)
        )
        if invoice_type != InvoiceType.TWO_DAYS:
            members = members.exclude(days=2)

        return members

    @staticmethod
    def create_email(
        invoice, template="emails/send_invoice_email.html", reminder=False
    ):
        subject = f"Factuur contributie {date.today().year} De Jonge Onderzoekers"
        if reminder:
            subject = f"Herinnering: {subject}"

        # Send to own address by default
        if invoice.member.email_ouders == "":
            recipients = [invoice.member.email_address]
        else:
            recipients = invoice.member.email_ouders.split(",")
            # Also send to senior member's own address
            if invoice.member.is_senior():
                recipients.append(invoice.member.email_address)

        send_to_parents = invoice.member.is_stripcard() or invoice.member.is_standard()
        body = render_to_string(
            template, context={"invoice": invoice, "send_to_parents": send_to_parents}
        )

        message = EmailMessage()
        message.from_email = settings.EMAIL_SENDER_INVOICE
        message.to = recipients
        message.bcc = settings.EMAIL_BCC
        message.subject = subject
        message.body = body
        message.content_subtype = "html"
        message.attach(invoice.invoice_number + ".pdf", invoice.pdf, "application/pdf")
        return message

    @staticmethod
    def send_by_email(invoice, reminder=False):
        if reminder:
            message = InvoiceTool.create_email(
                invoice, "emails/send_invoice_reminder.html", reminder=True
            )
        else:
            message = InvoiceTool.create_email(invoice)
        return message.send(fail_silently=False)

    @staticmethod
    def create_invoice(
        invoice_type: InvoiceType,
        member: Member,
        lines: list[InvoiceLine],
        creator: str,
    ):
        invoice = Invoice()
        invoice.member = member
        invoice.amount = InvoiceTool.calculate_grand_total(lines)
        invoice.amount_payed = 0.00
        invoice.created = timezone.now()
        invoice.username = creator
        invoice.save()
        invoice.pdf = InvoiceTool.render_invoice(
            member,
            lines,
            invoice.invoice_number,
            invoice_type,
        )
        invoice.save()
