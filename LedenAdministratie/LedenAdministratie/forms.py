from django import forms
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
from .models import Member, MemberType, Note, Invoice
from datetime import date


class LoginForm(forms.Form):
    username = forms.CharField(label='Gebruikersnaam', max_length=50, min_length=1)
    password = forms.CharField(label='Password', max_length=50, min_length=1, widget=forms.PasswordInput)


class MemberForm(forms.ModelForm):
    foto = forms.FileField(required=False)
    gebdat = forms.DateField(widget=forms.DateInput(format='%d-%m-%Y'), input_formats=settings.DATETIME_INPUT_FORMATS)
    aanmeld_datum = forms.DateField(widget=forms.DateInput(format='%d-%m-%Y'), input_formats=settings.DATETIME_INPUT_FORMATS,
                                    initial=date.today())
    afmeld_datum = forms.DateField(widget=forms.DateInput(format='%d-%m-%Y'), input_formats=settings.DATETIME_INPUT_FORMATS,
                                   required=False)

    class Meta:
        model = Member
        exclude = ['thumbnail']

    def save(self, commit=True):
        if 'foto' in self.changed_data:
            data = self.cleaned_data['foto']
            if isinstance(data, UploadedFile):
                data = data.file.read()
            self.instance.foto = data
            # Force re-gen of thumbnail
            self.instance.thumbnail = None
        return super().save(commit)


class ExportForm(forms.Form):
    filter_slug = forms.ModelChoiceField(label='Filter', required=True, queryset=MemberType.objects.all())


class LidNoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['text', 'done']


class InvoiceCreateForm(forms.Form):
    TYPES = (
        ('standaard', 'Standaard factuur voor 1 jaar'),
        ('senior', 'Senior Lid factuur voor 1 jaar'),
        ('maart', 'Factuur voor lid ingeschreven na 1 Maart'),
        ('sponsor', 'Sponsor factuur'),
        ('strippenkaart', 'Factuur voor lid met strippenkaart'),
        ('custom', 'Aangepaste factuur')
    )

    invoice_types = forms.ChoiceField(choices=TYPES)
    members = forms.ModelMultipleChoiceField(queryset=Member.objects.all(),
                                             widget=forms.CheckboxSelectMultiple)


class InvoiceLineForm(forms.Form):
    description = forms.CharField(max_length=200, required=False)
    count = forms.IntegerField()
    amount = forms.DecimalField(max_digits=7, decimal_places=2)


class InvoicePartialPaymentForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['amount_payed']


class InvoiceSelectionForm(forms.Form):
    invoices = forms.ModelMultipleChoiceField(queryset=Invoice.objects.all(),
                                              widget=forms.CheckboxSelectMultiple)
