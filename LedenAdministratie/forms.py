from django import forms
from LedenAdministratie.models import Lid
from captcha.fields import CaptchaField


class LoginForm(forms.Form):
    username = forms.CharField(label='Gebruikersnaam', max_length=50, min_length=1)


class LidForm(forms.ModelForm):
    captcha = CaptchaField()
    class Meta:
        model = Lid
        exclude = []
