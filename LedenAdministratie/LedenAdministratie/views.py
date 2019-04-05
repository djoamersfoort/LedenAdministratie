from django.contrib.auth import logout, login as auth_login
from django.contrib.auth.models import User
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView, BaseDetailView, View
from django.views.generic.list import ListView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse_lazy, reverse
from django.forms import formset_factory
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.db.models import F, Q
from requests_oauthlib import OAuth2Session
from . import settings
from .templatetags.photo_filter import img2base64
import csv
import uuid
from datetime import datetime, date

from .models import Member, MemberType, Note, Invoice
from . import forms
from .invoice import InvoiceTool
from .mixins import PermissionRequiredMixin, ApiPermissionRequired


class LoginView(View):
    def get(self, request, *args, **kwargs):
        oauth = OAuth2Session(client_id=settings.IDP_CLIENT_ID,
                              redirect_uri=settings.IDP_REDIRECT_URL,
                              scope=['user/basic', 'user/account-type', 'user/names', 'user/email'])
        auth_url, state = oauth.authorization_url(settings.IDP_AUTHORIZE_URL)
        return HttpResponseRedirect(auth_url)


class LoginResponseView(View):
    def get(self, request, *args, **kwargs):
        oauth = OAuth2Session(client_id=settings.IDP_CLIENT_ID,
                              redirect_uri=settings.IDP_REDIRECT_URL)
        full_response_url = request.build_absolute_uri()
        full_response_url = full_response_url.replace('http:', 'https:')
        try:
            access_token = oauth.fetch_token(settings.IDP_TOKEN_URL,
                                             authorization_response=full_response_url,
                                             client_secret=settings.IDP_CLIENT_SECRET)
        except:
            # Something went wrong getting the token
            return HttpResponseForbidden('Geen toegang')

        if 'access_token' in access_token and access_token['access_token'] != '':
            user_profile = oauth.get(settings.IDP_API_URL).json()
            username = "idp-{0}".format(user_profile['result']['id'])
            if settings.IDP_REQUIRED_ROLE not in user_profile['result']['accountType'].lower():
                return HttpResponseForbidden('Verplichte rol niet toegekend')

            try:
                found_user = User.objects.get(username=username)
            except User.DoesNotExist:
                found_user = User()
                found_user.username = username
                found_user.password = uuid.uuid4()
                found_user.email = user_profile['result']['email']
                found_user.first_name = user_profile['result']['firstName']
                found_user.last_name = user_profile['result']['lastName']
                found_user.is_superuser = True
                found_user.save()

            auth_login(request, found_user)

            return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)
        else:
            return HttpResponseForbidden('IDP Login mislukt')


class LogoffView(PermissionRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        logout(request)
        return HttpResponse(content='Uitgelogd')


class MemberListView(PermissionRequiredMixin, ListView):
    template_name = 'memberlist.html'
    required_permission = 'LedenAdministratie.view_member'

    def get_queryset(self):
        queryset = Member.objects.filter(Q(afmeld_datum__gt=date.today()) | Q(afmeld_datum=None))
        filter_slug = self.kwargs.get('filter_slug', '')
        if filter_slug != '':
            queryset = queryset.filter(types__slug=filter_slug)

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
        return reverse('members')


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
        form.instance.username = self.request.user.first_name
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
            invoice.username = self.request.user.first_name
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
    queryset = Invoice.objects.filter(amount_payed__lt=F('amount')).filter(member__isnull=False)
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


class InvoiceSendView(PermissionRequiredMixin, FormView):
    template_name = 'invoice_send.html'
    required_permission = 'LedenAdministratie.view_invoice'
    form_class = forms.InvoiceSelectionForm
    success_url = reverse_lazy('invoice_send')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['types'] = MemberType.objects.all()
        context['object_list'] = Invoice.objects.filter(amount_payed__lt=F('amount')).filter(member__isnull=False)
        return context

    def form_valid(self, form):
        invoices = form.cleaned_data['invoices']
        is_reminder = 'reminder' in self.request.POST
        for invoice in invoices:
            try:
                count = InvoiceTool.send_by_email(invoice, is_reminder)
                if count == 1:
                    invoice.sent = datetime.now()
                    invoice.smtp_error = None
                else:
                    invoice.smtp_error = "Fout bij versturen!"
            except Exception as e:
                invoice.smtp_error = "Fout bij versturen: " + str(e)

            invoice.save()
        return super().form_valid(form)


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

        members = Member.objects.filter(Q(afmeld_datum__gt=datetime.now()) | Q(afmeld_datum=None))
        if filter_slug != 'all':
            members = members.filter(types__slug=filter_slug)

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


@method_decorator(csrf_exempt, name='dispatch')
class ApiV1Smoelenboek(ApiPermissionRequired, View):
    def get(self, request, *args, **kwargs):
        members = Member.objects.filter(Q(afmeld_datum__gt=datetime.now()) | Q(afmeld_datum=None))
        day = self.kwargs.get('day', None)
        if day:
            if day == 'vrijdag':
                members = members.filter(dag_vrijdag=True)
            else:
                members = members.filter(dag_zaterdag=True)

        members = members.order_by('first_name')

        response = {'vrijdag': [], 'zaterdag': []}
        for member in members:
            photo = member.thumbnail
            if photo is None:
                photo = member.foto

            memberdict = {
                "id": member.id,
                "first_name": member.first_name,
                "last_name": member.last_name,
                "photo": img2base64(photo)
            }

            if member.dag_vrijdag:
                response['vrijdag'].append(memberdict)
            if member.dag_zaterdag:
                response['zaterdag'].append(memberdict)

        return JsonResponse(data=response)


@method_decorator(csrf_exempt, name='dispatch')
class ApiV1IDPGetDetails(View):
    def post(self, request, *args, **kwargs):
        userid = request.POST.get('user-id', '0').strip('u-')
        if not userid:
            return JsonResponse(data={'ok': False, 'error': 'User-id required'}, status=412)
        try:
            member = Member.objects.get(id=userid)
        except Member.DoesNotExist:
            return JsonResponse(data={'ok': False, 'error': 'User not found'}, status=404)

        response = {'user-id': member.id}
        fields = self.kwargs['fields'].split(',')
        for field in fields:
            if field == 'is-member':
                response['is-member'] = (member.afmeld_datum is None or member.afmeld_datum > datetime.now())
            elif field == 'mail':
                response['mail'] = member.email_address
            elif field == 'mail-parents':
                response['mail-parents'] = member.email_ouders
            elif field == 'city':
                response['city'] = member.woonplaats
            elif field == 'zip':
                response['zip'] = member.postcode
            elif field == 'address':
                response['address'] = member.straat
            elif field == 'phone':
                response['phone'] = member.telnr_ouders
            elif field == 'mobile':
                response['mobile'] = member.telnr
            elif field == 'firstname':
                response['firstname'] = member.first_name
            elif field == 'lastname':
                response['lastname'] = member.last_name
            elif field == 'middlename':
                response['middelname'] = ''
            elif field == 'dob':
                response['dob'] = member.gebdat
            elif field == 'type':
                response['type'] = ','.join([membertype.slug for membertype in member.types.all()])

        result = {'ok': True, 'result': response}
        return JsonResponse(data=result)


@method_decorator(csrf_exempt, name='dispatch')
class ApiV1IDPVerify(View):
    def post(self, request, *args, **kwargs):
        result = Member.objects.filter(Q(afmeld_datum__gt=date.today()) | Q(afmeld_datum=None))

        fields = self.kwargs['fields'].split(',')
        for field in fields:
            value = request.POST.get('email', 'xxxxx').lower()
            if field == 'email':
                result = result.filter(Q(email_address=value) | Q(email_ouders=value))
            elif field == 'zip':
                value = request.POST.get('zip', 'xxxxxx').lower().replace(' ', '')
                result = result.filter(postcode=value)

        try:
            member = result.get()
        except (Member.DoesNotExist, Member.MultipleObjectsReturned):
            return JsonResponse(data={'ok': False, 'result': None})

        return JsonResponse(data={'ok': True, 'result': 'u-{0}'.format(member.id)})


@method_decorator(csrf_exempt, name='dispatch')
class ApiV1IDPAvatar(View):
    def post(self, request, *args, **kwargs):
        return JsonResponse(data={'ok': False, 'error': 'Not implemented'}, status=200)
