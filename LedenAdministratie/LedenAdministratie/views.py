from django.shortcuts import render, redirect
from django.contrib.auth import logout, login as auth_login, authenticate
from django.contrib.auth.decorators import user_passes_test
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.mail import send_mail
from django.template.loader import render_to_string
import django.http
import csv

from .models import Member, MemberType, Note
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


class MemberListView(UserPassesTestMixin, ListView):
    template_name = 'ledenlijst.html'

    def get_queryset(self):
        queryset = Member.objects.proper_lastname_order()
        filter_slug = self.kwargs.get('filter_slug', '')
        if filter_slug != '':
            queryset = Member.objects.proper_lastname_order(types__slug=filter_slug)

        self.extra_context = {'types': MemberType.objects.all(), 'count': len(queryset), 'filter_slug': filter_slug}

        return queryset

    def test_func(self):
        return check_user(self.request.user)


class LidUpdateView(UserPassesTestMixin, UpdateView):
    model = Member
    template_name = 'edit_lid.html'
    form_class = forms.LidForm
    extra_context = {'types': MemberType.objects.all()}

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
        return reverse_lazy('ledenlijst')

    def form_valid(self, form):
        subject = 'Update ledenlijst van DJO'
        body = render_to_string('edit_lid_email.html', context={'lid': form.instance, 'oldlid': form.initial})
        if settings.SEND_UPDATE_EMAILS:
            send_mail(subject=subject, message=body, from_email=settings.EMAIL_SENDER,
                      recipient_list=settings.EMAIL_RECIPIENTS_UPDATE)
        return super(LidUpdateView, self).form_valid(form)


class LidCreateView(UserPassesTestMixin, CreateView):
    model = Member
    template_name = 'edit_lid.html'
    success_url = reverse_lazy('ledenlijst')
    form_class = forms.LidForm
    extra_context = {'types': MemberType.objects.all()}

    def test_func(self):
        can_change = self.request.user.has_perm('LedenAdministratie.change_lid')
        return check_user(self.request.user) and can_change


class LidDeleteView(UserPassesTestMixin, DeleteView):
    model = Member
    success_url = reverse_lazy('ledenlijst')
    template_name = 'delete_lid.html'
    fields = ['fist_name', 'last_name']
    extra_context = {'types': MemberType.objects.all()}

    def test_func(self):
        can_change = self.request.user.has_perm('LedenAdministratie.change_lid')
        return check_user(self.request.user) and can_change


class LidAddNoteView(UserPassesTestMixin, CreateView):
    model = Note
    form_class = forms.LidNoteForm
    template_name = 'lid_note.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['member'] = Member.objects.get(pk=self.kwargs['member_id'])
        return context

    def get_success_url(self):
        return reverse('lid_edit', kwargs={'pk': self.kwargs['member_id']})

    def form_valid(self, form):
        member_id = self.kwargs['member_id']
        form.instance.member = Member.objects.get(pk=member_id)
        form.instance.username = self.request.user.username
        return super().form_valid(form)

    def test_func(self):
        can_change = self.request.user.has_perm('LedenAdministratie.change_lid')
        return check_user(self.request.user) and can_change


class LidDeleteNoteView(UserPassesTestMixin, DeleteView):
    model = Note

    def get_success_url(self):
        return reverse('lid_edit', kwargs={'pk': self.object.member.id})

    def test_func(self):
        can_change = self.request.user.has_perm('LedenAdministratie.change_lid')
        return check_user(self.request.user) and can_change


class LidEditNoteView(UserPassesTestMixin, UpdateView):
    model = Note
    form_class = forms.LidNoteForm
    template_name = 'lid_note.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['member'] = self.object.member
        return context

    def get_success_url(self):
        return reverse('lid_edit', kwargs={'pk': self.object.member.id})

    def test_func(self):
        can_change = self.request.user.has_perm('LedenAdministratie.change_lid')
        return check_user(self.request.user) and can_change


class TodoListView(UserPassesTestMixin, ListView):
    model = Note
    template_name = 'todo_list.html'

    def get_queryset(self):
        todos = Note.objects.filter(done=False)
        self.extra_context = {'count': todos.count()}
        return todos

    def test_func(self):
        return check_user(self.request.user)


@user_passes_test(check_user)
def export(request):
    form = forms.ExportForm()
    if request.method == 'POST':
        form = forms.ExportForm(request.POST)
        if form.is_valid():
            filter_slug = form.cleaned_data['filter_slug']
            return redirect('do_export', filter_slug)

    return render(request, 'export.html', context={'form': form, 'types': MemberType.objects.all()})


@user_passes_test(check_user)
def do_export(request, filter_slug):
    if filter_slug == 'all':
        members = Member.objects.proper_lastname_order()
    else:
        members = Member.objects.proper_lastname_order(types__slug__in=filter_slug)

    filename = filter_slug + ".csv"
    response = django.http.HttpResponse(content_type='text/csv', charset='utf-8')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename

    writer = csv.writer(response, dialect=csv.excel, quoting=csv.QUOTE_ALL)
    writer.writerow(
        ['Voornaam', 'Achternaam', 'Geb. Datum', 'Leeftijd', 'Geslacht', 'E-mail', 'Straat',
         'Postcode', 'Woonplaats', 'Telnr', 'Telnr Ouders', 'E-mail Ouders'])

    for member in members:
        writer.writerow([member.first_name, member.last_name, member.gebdat, member.age, member.geslacht,
                         member.email_address, member.straat, member.postcode, member.woonplaats, member.telnr,
                         member.telnr_ouders, member.email_ouders])

    return response
