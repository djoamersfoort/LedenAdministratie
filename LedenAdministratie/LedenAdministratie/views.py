from django.shortcuts import render, redirect
from django.contrib.auth import logout, login as auth_login, authenticate
from django.contrib.auth.decorators import user_passes_test
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.mail import send_mail
from django.template.loader import render_to_string
import django.http
import csv

from .models import Lid
from . import forms
from . import settings


def login(request, template_name='login.html'):
    form = forms.LoginForm()

    if request.method == 'POST':
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user and user.is_active:
                auth_login(request, user)
                return redirect('ledenlijst')

    return render(request, 'login.html', {'form': form})


def check_user(user):
    if user.is_authenticated and user.has_perm('LedenAdministratie.read_lid') and user.is_active:
        return True
    return False


@user_passes_test(check_user)
def logoff(request):
    logout(request)

    return redirect('/')


@user_passes_test(check_user)
def ledenlijst(request, speltak='nieuw'):
    if speltak == 'nieuw':
        leden = Lid.objects.filter(speltak=speltak).order_by('aanmeld_datum')
    else:
        leden = Lid.objects.proper_lastname_order(speltak=speltak)

    return render(request, 'ledenlijst.html', {'leden': leden, 'speltak': speltak, 'speltakken': Lid.LIJST_CHOICES, 'count': len(leden)})


class LidUpdateView(UserPassesTestMixin, UpdateView):
    model = Lid
    template_name = 'edit_lid.html'
    form_class = forms.LidForm

    def get_form(self, form_class=None):
        form = super(LidUpdateView, self).get_form(form_class)

        # Make the form read-only when user has no change permissions
        if not self.request.user.has_perm('LedenAdministratie.change_lid'):
            for name, field in form.fields.items():
                field.widget.attrs['disabled'] = True
        return form

    def test_func(self):
        return check_user(self.request.user)

    def get_success_url(self):
        url = "%s%s/" % (reverse_lazy('ledenlijst'), self.object.speltak)
        return url

    def form_valid(self, form):
        subject = 'Update ledenlijst van DJO'
        body = render_to_string('edit_lid_email.html', context={'lid': form.instance, 'oldlid': form.initial})
        if settings.SEND_UPDATE_EMAILS:
            send_mail(subject=subject, message=body, from_email=settings.EMAIL_SENDER,
                      recipient_list=settings.EMAIL_RECIPIENTS_UPDATE)
        return super(LidUpdateView, self).form_valid(form)


class LidCreateView(UserPassesTestMixin, CreateView):
    model = Lid
    template_name = 'edit_lid.html'
    success_url = reverse_lazy('ledenlijst')
    form_class = forms.LidForm

    def test_func(self):
        can_change = self.request.user.has_perm('LedenAdministratie.change_lid')
        return check_user(self.request.user) and can_change

    def get_success_url(self):
        url = "%s%s/" % (reverse_lazy('ledenlijst'), self.object.speltak)
        return url


class LidAanmeldView(CreateView):
    model = Lid
    form_class = forms.LidCaptchaForm
    template_name = 'aanmelden_lid.html'
    success_url = reverse_lazy('aanmelden_ok')

    def form_valid(self, form):
        if settings.SEND_NEW_EMAILS:
            # Send an e-mail to 'bestuur'
            subject = 'Nieuwe aanmelding DJO ontvangen'
            body = render_to_string('aanmelden_email.html', context={'lid': form.instance})
            send_mail(subject=subject, message=body, from_email=settings.EMAIL_SENDER,
                      recipient_list=settings.EMAIL_RECIPIENTS_NEW)

            # Send a confirmation e-mail to the user
            subject = 'Bevestiging aanmelding DJO'
            body = render_to_string('aanmelden_email_user.html', context={'lid': form.instance})
            send_mail(subject=subject, message=body, from_email=settings.EMAIL_SENDER,
                      recipient_list=[form.instance.email_address])

        return super(LidAanmeldView, self).form_valid(form)


def aanmelden_ok(request):
    return render(request, 'aanmelden_ok.html')


class LidDeleteView(UserPassesTestMixin, DeleteView):
    model = Lid
    success_url = reverse_lazy('ledenlijst')
    template_name = 'delete_lid.html'
    fields = ['fist_name', 'last_name']

    def test_func(self):
        can_change = self.request.user.has_perm('LedenAdministratie.change_lid')
        return check_user(self.request.user) and can_change


@user_passes_test(check_user)
def export(request):
    form = forms.ExportForm()
    if request.method == 'POST':
        form = forms.ExportForm(request.POST)
        if form.is_valid():
            speltak = form.cleaned_data['speltak']
            return redirect('do_export', speltak)

    return render(request, 'export.html', context={'form': form, 'speltakken': Lid.LIJST_CHOICES})


@user_passes_test(check_user)
def do_export(request, speltak):
    if speltak == 'all':
        leden = Lid.objects.proper_lastname_order()
    else:
        leden = Lid.objects.proper_lastname_order(speltak=speltak)

    filename = speltak + ".csv"
    response = django.http.HttpResponse(content_type='text/csv', charset='utf-8')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename

    writer = csv.writer(response, dialect=csv.excel, quoting=csv.QUOTE_ALL)
    writer.writerow(
        ['Voornaam', 'Achternaam', 'Geb. Datum', 'Leeftijd', 'Geslacht', 'Lijst', 'E-mail', 'Straat',
         'Postcode', 'Woonplaats', 'Telnr', 'Mobiel', 'Mobiel Ouder 1', 'Mobiel Ouder 2',
         'E-mail Ouder 1', 'E-mail Ouder 2'])

    for lid in leden:
        writer.writerow([lid.first_name, lid.last_name, lid.gebdat, lid.age, lid.geslacht, lid.speltak,
                         lid.email_address, lid.straat, lid.postcode, lid.woonplaats, lid.telnr,
                         lid.mobiel, lid.mobiel_ouder1, lid.mobiel_ouder2, lid.email_ouder1, lid.email_ouder2])

    return response
