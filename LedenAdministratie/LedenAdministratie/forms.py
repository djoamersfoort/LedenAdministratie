from django import forms
from .models import Member, MemberType
from captcha.fields import CaptchaField


class LoginForm(forms.Form):
    username = forms.CharField(label='Gebruikersnaam', max_length=50, min_length=1)
    password = forms.CharField(label='Password', max_length=50, min_length=1, widget=forms.PasswordInput)


class LidForm(forms.ModelForm):
    class Meta:
        model = Member
        exclude = []


class LidCaptchaForm(forms.ModelForm):
    captcha = CaptchaField()

    class Meta:
        model = Member
        exclude = []


class ExportForm(forms.Form):
    filter_slug = forms.ModelChoiceField(label='Filter', required=True, queryset=MemberType.objects.all())
