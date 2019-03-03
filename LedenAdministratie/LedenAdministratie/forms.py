from django import forms
from django.forms.fields import validators
from django.core.files.uploadedfile import UploadedFile
from .models import Member, MemberType, Note, Invoice
from captcha.fields import CaptchaField


class LoginForm(forms.Form):
    username = forms.CharField(label='Gebruikersnaam', max_length=50, min_length=1)
    password = forms.CharField(label='Password', max_length=50, min_length=1, widget=forms.PasswordInput)


class LidForm(forms.ModelForm):
    foto = forms.FileField(required=False)

    class Meta:
        model = Member
        exclude = []

    def save(self, commit=True):
        if self.cleaned_data.get('foto') is not None:
            data = self.cleaned_data['foto']
            if isinstance(data, UploadedFile):
                data = data.file.read()
            self.instance.foto = data
        return super().save(commit)


class LidCaptchaForm(forms.ModelForm):
    captcha = CaptchaField()

    class Meta:
        model = Member
        exclude = []


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
        ('custom', 'Aangepaste factuur')
    )

    invoice_types = forms.ChoiceField(choices=TYPES)
    members = forms.ModelMultipleChoiceField(queryset=Member.objects.all(),
                                             widget=forms.CheckboxSelectMultiple)


class InvoiceLineForm(forms.Form):
    description = forms.CharField(max_length=200, required=False)
    count = forms.IntegerField()
    amount = forms.DecimalField(max_digits=7, decimal_places=2)
