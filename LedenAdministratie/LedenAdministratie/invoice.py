from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.db.models import Q
from django.conf import settings
from datetime import date, timedelta
from weasyprint import HTML, CSS, default_url_fetcher
from weasyprint.fonts import FontConfiguration
from decimal import Decimal
from .models import Member
from .utils import Utils

import os


class InvoiceTool:

    @staticmethod
    def calculate_grand_total(lines):
        grand_total = 0
        for line in lines:
            if 'count' in line.cleaned_data and 'amount' in line.cleaned_data:
                grand_total += line.cleaned_data['count'] * line.cleaned_data['amount']
        return grand_total

    @staticmethod
    def invoice_url_fetcher(url, timeout=10):
        if url.startswith('local:'):
            parts = url.split(':')
            path = parts[1]
            mime_type = parts[2]
            path = os.path.join(settings.BASE_DIR, path)
            file_obj = open(path, "rb")
            return dict(file_obj=file_obj, mime_type=mime_type)
        else:
            return default_url_fetcher(url, timeout)

    @staticmethod
    def render_invoice(member, lines, invoice_number, invoice_type):
        invoice_date = date.today().strftime('%d-%m-%Y')
        due_date = (date.today() + timedelta(days=14)).strftime('%d-%m-%Y')
        extra_text = InvoiceTool.get_extra_text_for_invoice_type(invoice_type)
        title = InvoiceTool.get_title_for_invoice_type(invoice_type)

        grand_total = 0
        valid_lines = []
        for line in lines:
            if 'count' in line.cleaned_data and 'amount' in line.cleaned_data:
                line_total = line.cleaned_data['count'] * line.cleaned_data['amount']
                grand_total += line.cleaned_data['count'] * line.cleaned_data['amount']
                valid_lines.append(dict(
                    amount=line.cleaned_data['amount'],
                    count=line.cleaned_data['count'],
                    description=line.cleaned_data['description'],
                    line_total=line_total
                ))

        font_config = FontConfiguration()
        strcss = render_to_string('invoice/invoice.css')
        css = CSS(string=strcss, font_config=font_config)
        html = render_to_string('invoice/invoice.html',
                                context={'lines': valid_lines,
                                         'extra_text': extra_text,
                                         'member': member,
                                         'invoicenr': invoice_number,
                                         'title': title,
                                         'date': invoice_date,
                                         'due_date': due_date,
                                         'grand_total': grand_total})
        printer = HTML(string=html, url_fetcher=InvoiceTool.invoice_url_fetcher)
        return printer.write_pdf(stylesheets=[css])

    @staticmethod
    def get_title_for_invoice_type(invoice_type):
        title = 'Aan de ouders/verzorgers van:'
        if invoice_type in ['sponsor', 'custom', 'senior']:
            title = 'Aan:'
        return title

    @staticmethod
    def get_extra_text_for_invoice_type(invoice_type):
        extra_text = ''
        if invoice_type in ['standaard', '2dagen', 'senior'] and date.today() < date(date.today().year, 5, 1):
            extra_text = "Het is mogelijk om in 2 termijnen te betalen\n" \
                         "De eerste helft zal binnen 14 dagen overgemaakt moeten worden.\n" \
                         "Het tweede deel zal uiterlijk 31 mei overgemaakt moeten worden."
        return extra_text

    @staticmethod
    def get_defaults_for_invoice_type(invoice_type):
        defaults = [{
            'description': 'Contributie {0} DJO Amersfoort'.format(date.today().year),
            'count': 1,
            'amount': Utils.get_setting('invoice_amount_year')}]

        if invoice_type == 'senior':
            defaults = [{
                'description': 'Contributie senior lid {0} DJO Amersfoort'.format(date.today().year),
                'count': 1,
                'amount': Utils.get_setting('invoice_amount_year_senior')}]
        elif invoice_type == 'maart':
            defaults = [{
                    'description': 'Contributie {0} DJO Amersfoort'.format(date.today().year),
                    'count': 1,
                    'amount': Utils.get_setting('invoice_amount_year')
                },
                {
                    'description': 'Correctie vanwege ingangsdatum - -{0}'.format(date.today().year),
                    'count': -1,
                    'amount':  Utils.get_setting('invoice_amount_month')
                },
            ]
        elif invoice_type == 'strippenkaart':
            defaults = [
            {
                'description': 'Strippenkaart {0} DJO Amersfoort'.format(date.today().year),
                'count': 10,
                'amount': Utils.get_setting('invoice_amount_day')
            }
        ]
        elif invoice_type == 'sponsor':
            defaults = [
                {
                    'description': 'Sponsor {0} DJO Amersfoort'.format(date.today().year),
                    'count': 1,
                    'amount': Utils.get_setting('invoice_amount_sponsor')
                }
            ]
        elif invoice_type == '2dagen':
            defaults = [
                {
                    'description': 'Contributie {0} DJO Amersfoort'.format(date.today().year),
                    'count': 1,
                    'amount': Utils.get_setting('invoice_amount_year')
                },
                {
                    'description': 'Toeslag voor deelname op beide dagen'.format(date.today().year),
                    'count': 1,
                    'amount': float(Utils.get_setting('invoice_amount_year')) / 2
                },
            ]
        elif invoice_type == 'custom':
            defaults = []

        return defaults

    @staticmethod
    def get_members_invoice_type(invoice_type):
        members = Member.objects.filter(types__slug='member', aanmeld_datum__lt=date(date.today().year, 3, 1))
        if invoice_type == 'senior':
            members = Member.objects.filter(types__slug='senior')
        elif invoice_type == 'sponsor':
            members = Member.objects.filter(types__slug='sponsor')
        elif invoice_type == 'maart':
            members = Member.objects.filter(types__slug='member', aanmeld_datum__gt=date(date.today().year, 2, 28))
        elif invoice_type == 'strippenkaart':
            members = Member.objects.filter(types__slug='strippenkaart')
        elif invoice_type == '2dagen':
            members = Member.objects.filter(types__slug='member', dag_vrijdag=True, dag_zaterdag=True)
        elif invoice_type == 'custom':
            members = Member.objects.all()

        # Only return active members
        members = members.filter(Q(afmeld_datum__gt=date.today()) | Q(afmeld_datum=None))
        if invoice_type != '2dagen':
            members = members.exclude(dag_vrijdag=True, dag_zaterdag=True)

        return members

    @staticmethod
    def create_email(invoice, template='emails/send_invoice_email.html', reminder=False):
        member_types = [member_type.slug for member_type in invoice.member.types.all()]
        subject = 'Factuur contributie {0} De Jonge Onderzoekers'.format(date.today().year)
        if reminder:
            subject = 'Herinnering: {0}'.format(subject)
        body = render_to_string(template, context={'invoice': invoice, 'member_types': member_types})

        # Send to own address by default
        if invoice.member.email_ouders == '':
            recipients = [invoice.member.email_address]
        else:
            recipients = invoice.member.email_ouders.split(',')
            # Also send to senior member's own address
            if invoice.member.is_senior():
                recipients.append(invoice.member.email_address)

        message = EmailMessage()
        message.from_email = settings.EMAIL_SENDER_INVOICE
        message.to = recipients
        message.bcc = settings.EMAIL_BCC
        message.subject = subject
        message.body = body
        message.content_subtype = 'html'
        message.attach(invoice.invoice_number+".pdf", invoice.pdf, 'application/pdf')
        return message

    @staticmethod
    def send_by_email(invoice, reminder=False):
        if reminder:
            message = InvoiceTool.create_email(invoice, 'emails/send_invoice_reminder.html', reminder=True)
        else:
            message = InvoiceTool.create_email(invoice)
        return message.send(fail_silently=False)
