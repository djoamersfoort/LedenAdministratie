from django.template.loader import render_to_string, get_template
from datetime import date, timedelta
from weasyprint import HTML, CSS
from weasyprint.fonts import FontConfiguration


class InvoiceTool:

    @staticmethod
    def calculate_grand_total(lines):
        grand_total = 0
        for line in lines:
            if 'count' in line.cleaned_data and 'amount' in line.cleaned_data:
                grand_total += line.cleaned_data['count'] * line.cleaned_data['amount']
        return grand_total

    @staticmethod
    def render_invoice(member, lines, invoice_number):
        invoice_date = date.today().strftime('%d-%m-%Y')
        due_date = (date.today() + timedelta(days=14)).strftime('%d-%m-%Y')

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
                                         'member': member,
                                         'invoicenr': invoice_number,
                                         'date': invoice_date,
                                         'due_date': due_date,
                                         'grand_total': grand_total})
        printer = HTML(string=html)
        return printer.write_pdf(stylesheets=[css])
