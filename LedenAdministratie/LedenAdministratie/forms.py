from django import forms
from .models import Member, MemberType, Note
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
            data = self.cleaned_data['foto'].file.read()
            self.instance.foto = data
        return super().save(commit)


class LidCaptchaForm(forms.ModelForm):
    captcha = CaptchaField()

    class Meta:
        model = Member
        exclude = []


class ExportForm(forms.Form):
    filter_slug = forms.ModelChoiceField(label='Filter', required=True, queryset=MemberType.objects.all())


class LidAddNoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['text']
