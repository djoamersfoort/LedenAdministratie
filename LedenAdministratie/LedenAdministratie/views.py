from django.contrib.auth import logout, login as auth_login, authenticate
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView, BaseDetailView, View
from django.views.generic.list import ListView
from django.urls import reverse_lazy, reverse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.forms import formset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import F
import csv
from datetime import datetime

from .models import Member, MemberType, Note, Invoice
from . import forms, settings
from .invoice import InvoiceTool
from .mixins import PermissionRequiredMixin


class LoginView(FormView):
    form_class = forms.LoginForm
    template_name = 'login.html'

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)
        if user and user.is_active:
            auth_login(self.request, user)
            return HttpResponseRedirect(reverse('members'))
        else:
            return HttpResponseRedirect(reverse('login'))


class LogoffView(PermissionRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        logout(request)
        return HttpResponseRedirect('/')


class MemberListView(PermissionRequiredMixin, ListView):
    template_name = 'memberlist.html'
    required_permission = 'LedenAdministratie.view_member'

    def get_queryset(self):
        queryset = Member.objects.proper_lastname_order()
        filter_slug = self.kwargs.get('filter_slug', '')
        if filter_slug != '':
            queryset = Member.objects.proper_lastname_order(types__slug=filter_slug)

        self.extra_context = {'types': MemberType.objects.all(), 'count': len(queryset), 'filter_slug': filter_slug}

        return queryset


class MemberUpdateView(PermissionRequiredMixin, UpdateView):
    model = Member
    template_name = 'edit_member.html'
    form_class = forms.MemberForm
    extra_context = {'types': MemberType.objects.all()}
    required_permission = 'LedenAdministratie.change_member'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Make the form read-only when user has no change permissions
        if not self.request.user.has_perm('LedenAdministratie.change_lid'):
            for name, field in form.fields.items():
                field.widget.attrs['disabled'] = True
        return form

    def get_success_url(self):
        return reverse_lazy('members')

    def form_valid(self, form):
        subject = 'Update ledenlijst van DJO'
        body = render_to_string('edit_lid_email.html', context={'lid': form.instance, 'oldlid': form.initial})
        if settings.SEND_UPDATE_EMAILS:
            send_mail(subject=subject, message=body, from_email=settings.EMAIL_SENDER,
                      recipient_list=settings.EMAIL_RECIPIENTS_UPDATE)
        return super().form_valid(form)


class MemberCreateView(PermissionRequiredMixin, CreateView):
    model = Member
    template_name = 'edit_member.html'
    success_url = reverse_lazy('members')
    form_class = forms.MemberForm
    extra_context = {'types': MemberType.objects.all()}
    required_permission = 'LedenAdministratie.add_member'


class MemberDeleteView(PermissionRequiredMixin, DeleteView):
    model = Member
    success_url = reverse_lazy('members')
    template_name = 'delete_member.html'
    fields = ['fist_name', 'last_name']
    extra_context = {'types': MemberType.objects.all()}
    required_permission = 'LedenAdministratie.delete_member'


class MemberAddNoteView(PermissionRequiredMixin, CreateView):
    model = Note
    form_class = forms.LidNoteForm
    template_name = 'lid_note.html'
    required_permission = 'LedenAdministratie.add_note'

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


class MemberDeleteNoteView(PermissionRequiredMixin, View):
    required_permission = 'LedenAdministratie.delete_note'

    def get(self, request, *args, **kwargs):
        note = Note.objects.get(pk=kwargs['pk'])
        note.delete()
        if 'HTTP_REFERER' in request.META:
            url = request.META['HTTP_REFERER']
        else:
            url = reverse('members')
        return HttpResponseRedirect(url)


class MemberEditNoteView(PermissionRequiredMixin, UpdateView):
    model = Note
    form_class = forms.LidNoteForm
    template_name = 'lid_note.html'
    required_permission = 'LedenAdministratie.change_note'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['member'] = self.object.member
        return context

    def get_success_url(self):
        return reverse('lid_edit', kwargs={'pk': self.object.member.id})


class TodoListView(PermissionRequiredMixin, ListView):
    model = Note
    template_name = 'todo_list.html'
    required_permission = 'LedenAdministratie.view_note'

    def get_queryset(self):
        todos = Note.objects.filter(done=False)
        self.extra_context = {'types': MemberType.objects.all()}
        return todos


class InvoiceCreateView(PermissionRequiredMixin, FormView):
    template_name = 'invoice_create.html'
    form_class = forms.InvoiceCreateForm
    LinesFormSet = formset_factory(forms.InvoiceLineForm, extra=5)
    success_url = reverse_lazy('members')
    lines = None
    invoice_type = None
    refresh_only = False
    required_permission = 'LedenAdministratie.add_invoice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['types'] = MemberType.objects.all()

        if self.kwargs.get('member_id'):
            context['member'] = Member.objects.get(pk=self.kwargs['member_id'])
        else:
            context['form'].fields['members'].queryset = InvoiceTool.get_members_invoice_type(self.invoice_type)

        self.lines = self.LinesFormSet(initial=InvoiceTool.get_defaults_for_invoice_type(self.invoice_type))
        context['invoice_lines'] = self.lines

        return context

    def post(self, request, *args, **kwargs):
        self.lines = self.LinesFormSet(request.POST, request.FILES)
        if 'create' in request.POST:
            return super().post(request, *args, *kwargs)
        else:
            # Invoice type dropdown changed
            self.invoice_type = request.POST['invoice_types']
            form = self.get_form()
            form.errors.clear()
            return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, form):
        self.lines.is_valid()
        for member in form.cleaned_data['members']:
            invoice = Invoice()
            invoice.member = member
            invoice.amount = InvoiceTool.calculate_grand_total(self.lines)
            invoice.amount_payed = 0.00
            invoice.created = datetime.now()
            invoice.username = self.request.user.username
            invoice.save()
            invoice.pdf = InvoiceTool.render_invoice(member, self.lines, invoice.invoice_number,
                                                     form.cleaned_data['invoice_types'])
            invoice.save()
        return super().form_valid(form)


class InvoiceDisplayView(PermissionRequiredMixin, BaseDetailView):
    model = Invoice
    required_permission = 'LedenAdministratie.view_invoice'

    def get(self, request, *args, **kwargs):
        invoice = self.get_object()
        return HttpResponse(invoice.pdf, content_type='application/pdf')


class InvoiceDeleteView(PermissionRequiredMixin, View):
    required_permission = 'LedenAdministratie.delete_invoice'

    def get(self, request, *args, **kwargs):
        invoice = Invoice.objects.get(pk=kwargs['pk'])
        invoice.delete()
        if 'HTTP_REFERER' in request.META:
            url = request.META['HTTP_REFERER']
        else:
            url = reverse('members')
        return HttpResponseRedirect(url)


class InvoicePaymentView(PermissionRequiredMixin, ListView):
    model = Invoice
    queryset = Invoice.objects.filter(amount_payed__lt=F('amount'))
    template_name = 'invoice_payment.html'
    extra_context = {'types': MemberType.objects.all()}
    required_permission = 'LedenAdministratie.view_invoice'


class InvoicePayFullView(PermissionRequiredMixin, View):
    required_permission = 'LedenAdministratie.view_invoice'

    def get(self, request, *args, **kwargs):
        invoice = Invoice.objects.get(pk=kwargs['pk'])
        invoice.amount_payed = invoice.amount
        invoice.save()
        return HttpResponseRedirect(reverse('invoice_payment'))


class InvoicePayPartView(PermissionRequiredMixin, UpdateView):
    model = Invoice
    template_name = 'invoice_partial_payment.html'
    form_class = forms.InvoicePartialPaymentForm
    required_permission = 'LedenAdministratie.view_invoice'

    def get_success_url(self):
        if self.kwargs.get('member_id'):
            return reverse('lid_edit', kwargs={'pk': self.kwargs['member_id']})
        else:
            return reverse('invoice_payment')


class ExportView(PermissionRequiredMixin, FormView):
    form_class = forms.ExportForm
    template_name = 'export.html'
    required_permission = 'LedenAdministratie.view_member'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['types'] = MemberType.objects.all()
        return context

    def form_valid(self, form):
        filter_slug = form.cleaned_data['filter_slug'].slug

        print("Filter slug = {0}".format(filter_slug))
        if filter_slug == 'all':
            members = Member.objects.proper_lastname_order()
        else:
            members = Member.objects.proper_lastname_order(types__slug=filter_slug)

        filename = filter_slug + ".csv"
        response = HttpResponse(content_type='text/csv', charset='utf-8')
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
