from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from datetime import date, timedelta
from weasyprint import HTML, CSS, default_url_fetcher
from weasyprint.fonts import FontConfiguration
from . import settings
from .models import Member

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
        if invoice_type in ['sponsor', 'custom']:
            title = 'Aan:'
        return title

    @staticmethod
    def get_extra_text_for_invoice_type(invoice_type):
        extra_text = ''
        if invoice_type in ['standaard', 'senior']:
            extra_text = "Het is mogelijk om in 2 termijnen te betalen\n" \
                         "De eerste helft zal binnen 14 dagen overgemaakt moeten worden.\n" \
                         "Het tweede deel zal uiterlijk 31 mei overgemaakt moeten worden."
        return extra_text

    @staticmethod
    def get_defaults_for_invoice_type(invoice_type):
        defaults = [{
            'description': 'Contributie {0} DJO Amersfoort'.format(date.today().year),
            'count': 1,
            'amount': 165.00}]

        if invoice_type == 'senior':
            defaults = [{
                'description': 'Contributie senior lid {0} DJO Amersfoort'.format(date.today().year),
                'count': 1,
                'amount': 200.00}]
        elif invoice_type == 'maart':
            defaults = [{
                    'description': 'Contributie {0} DJO Amersfoort'.format(date.today().year),
                    'count': 1,
                    'amount': 165.00
                },
                {
                    'description': 'Correctie vanwege ingangsdatum - -{0}'.format(date.today().year),
                    'count': -1,
                    'amount': 13.75
                },
            ]
        elif invoice_type == 'sponsor':
            defaults = [
                {
                    'description': 'Sponsor {0} DJO Amersfoort'.format(date.today().year),
                    'count': 1,
                    'amount': 150.00
                }
            ]
        elif invoice_type == 'custom':
            defaults = []

        return defaults

    @staticmethod
    def get_members_invoice_type(invoice_type):
        members = Member.objects.filter(types__slug='member')
        if invoice_type == 'senior':
            members = Member.objects.filter(types__slug='senior')
        elif invoice_type == 'sponsor':
            members = Member.objects.filter(types__slug='sponsor')
        elif invoice_type == 'custom':
            members = Member.objects.all()
        return members

    @staticmethod
    def create_email(invoice, template='send_invoice_email.html'):
        member_types = [member_type.slug for member_type in invoice.member.types.all()]
        subject = 'Factuur contributie {0} De Jonge Onderzoekers'.format(date.today().year)
        body = render_to_string(template, context={'invoice': invoice, 'member_types': member_types})
        recipients = [invoice.member.email_address]
        if invoice.member.email_ouders != '':
            recipients = [invoice.member.email_ouders]
        message = EmailMessage()
        message.from_email = settings.EMAIL_SENDER
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
            message = InvoiceTool.create_email(invoice, 'send_invoice_reminder.html')
        else:
            message = InvoiceTool.create_email(invoice)
        return message.send()
