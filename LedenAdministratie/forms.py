from django import forms
from LedenAdministratie.models import Lid


class LoginForm(forms.Form):
    username = forms.CharField(label='Gebruikersnaam', max_length=50, min_length=1)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)


class LidForm(forms.ModelForm):
    class Meta:
        model = Lid
        exclude = []
