from django import forms
from LedenAdministratie.models import Lid
from captcha.fields import CaptchaField


class LoginForm(forms.Form):
    username = forms.CharField(label='Gebruikersnaam', max_length=50, min_length=1)


class LidForm(forms.ModelForm):
    class Meta:
        model = Lid
        exclude = []

class LidCaptchaForm(forms.ModelForm):
    captcha = CaptchaField()
    class Meta:
        model = Lid
        exclude = []

class ExportForm(forms.Form):
    choices = Lid.LIJST_CHOICES.copy()
    choices.insert(0, ('all', 'Alle Lijsten'))
    speltak = forms.ChoiceField(label='Speltak', choices=choices, required=True)
