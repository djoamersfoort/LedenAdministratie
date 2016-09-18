from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as do_login, logout
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import Lid
from . import forms
from . import settings


def login(request):
    form = forms.LoginForm()

    if request.method == 'POST':
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                do_login(request, user)
                return redirect('ledenlijst')

    return render(request, 'login.html', {'form': form})


@login_required()
def logoff(request):
    logout(request)
    return redirect('login')


@login_required
def index(request):
    return render(request, 'base.html')


@login_required
def ledenlijst(request, speltak='wachtlijst'):
    if speltak == 'wachtlijst':
        leden = Lid.objects.filter(speltak=speltak).order_by('aanmeld_datum')
    else:
        leden = Lid.objects.filter(speltak=speltak)
    return render(request, 'ledenlijst.html', {'leden': leden, 'speltak': speltak, 'speltakken': Lid.LIJST_CHOICES})


class LidUpdateView(LoginRequiredMixin, UpdateView):
    model = Lid
    template_name = 'edit_lid.html'
    fields = ['first_name', 'last_name', 'gebdat', 'speltak', 'email_address', 'straat', 'postcode', 'woonplaats',
              'telnr', 'mobiel', 'mobiel_ouder1', 'mobiel_ouder2', 'email_ouder1', 'email_ouder2', 'inschrijf_datum_sn',
              'scouting_nr', 'tshirt_maat', 'jub_badge', 'verzekerings_nr', 'opmerkingen', 'bijzonderheden', 'geslacht']

    def get_success_url(self):
        url = "%s%s/" %(reverse_lazy('ledenlijst'), self.object.speltak)
        return url

    def form_valid(self, form):
        subject = 'Update ledenlijst van scouting St Ansfridus'
        body = render_to_string('edit_lid_email.html', context={'lid': form.instance, 'oldlid': form.initial})
        send_mail(subject=subject, message=body, from_email=settings.EMAIL_SENDER, recipient_list=settings.EMAIL_RECIPIENTS_UPDATE)
        return super(LidUpdateView, self).form_valid(form)


class LidCreateView(LoginRequiredMixin, CreateView):
    model = Lid
    template_name = 'edit_lid.html'
    success_url = reverse_lazy('ledenlijst')
    fields = ['first_name', 'last_name', 'gebdat', 'speltak', 'email_address', 'straat', 'postcode', 'woonplaats',
              'telnr', 'mobiel', 'mobiel_ouder1', 'mobiel_ouder2', 'email_ouder1', 'email_ouder2', 'inschrijf_datum_sn',
              'scouting_nr', 'tshirt_maat', 'jub_badge', 'verzekerings_nr', 'opmerkingen', 'bijzonderheden', 'geslacht']

    def get_success_url(self):
        url = "%s%s/" % (reverse_lazy('ledenlijst'), self.object.speltak)
        return url

class LidAanmeldView(CreateView):
    model = Lid
    template_name = 'aanmelden_lid.html'
    success_url = reverse_lazy('aanmelden_ok')
    fields = ['first_name', 'last_name', 'gebdat', 'speltak', 'email_address', 'straat', 'postcode', 'woonplaats',
              'telnr', 'mobiel', 'mobiel_ouder1', 'mobiel_ouder2', 'email_ouder1', 'email_ouder2', 'geslacht']

    def form_valid(self, form):
        subject = 'Nieuwe aanmelding St. Ansfridus ontvangen'
        body = render_to_string('aanmelden_email.html', context={'lid': form.instance})
        send_mail(subject=subject, message=body, from_email=settings.EMAIL_SENDER, recipient_list=settings.EMAIL_RECIPIENTS_NEW)
        return super(LidAanmeldView, self).form_valid(form)


def aanmelden_ok(request):
    return render(request, 'aanmelden_ok.html')


class LidDeleteView(LoginRequiredMixin, DeleteView):
    model = Lid
    success_url = reverse_lazy('ledenlijst')
    template_name = 'delete_lid.html'
    fields = ['fist_name', 'last_name']
