import csv
from datetime import date

import requests
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import EmailMessage
from django.db.models import Q, F
from django.forms import formset_factory
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic.edit import (
    CreateView,
    UpdateView,
    DeleteView,
    FormView,
    BaseDetailView,
    View,
)
from django.views.generic.list import ListView
from mailer.models import MessageLog
from two_factor.views.mixins import OTPRequiredMixin

from LedenAdministratie import forms
from LedenAdministratie.invoice import InvoiceTool, InvoiceType, InvoiceLine
from LedenAdministratie.mixins import PermissionRequiredMixin
from LedenAdministratie.models import (
    Member,
    MemberType,
    Note,
    Invoice,
    Setting,
    Stripcard,
)
from LedenAdministratie.utils import Utils


class LoggedInView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if (
            request.user.has_perm("LedenAdministratie.view_member")
            and request.user.is_verified()
        ):
            return HttpResponseRedirect(reverse("members"))
        return HttpResponseRedirect(reverse("profile"))


class Profile(LoginRequiredMixin, UpdateView):
    template_name = "profile.html"
    form_class = forms.MemberForm
    model = Member

    def post(self, request, *args, **kwargs):
        return HttpResponseForbidden()

    def get_object(self, queryset=None):
        return self.request.user.member

    def get_form(self, form_class=None):
        form = super().get_form()

        # Make the form read-only
        for _, field in form.fields.items():
            field.widget.attrs["disabled"] = True

        return form


class MemberListView(OTPRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = "memberlist.html"
    required_permission = "LedenAdministratie.view_member"

    def get_queryset(self):
        queryset = Member.objects.filter(
            Q(afmeld_datum__gt=date.today()) | Q(afmeld_datum=None)
        )
        filter_slug = self.kwargs.get("filter_slug", "")

        if filter_slug == "inactive":
            queryset = Member.objects.filter(afmeld_datum__lte=date.today())
        elif filter_slug != "":
            queryset = queryset.filter(types__slug=filter_slug)

        self.extra_context = {
            "types": MemberType.objects.all(),
            "count": len(queryset),
            "filter_slug": filter_slug,
        }

        return queryset


class MemberUpdateView(OTPRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Member
    template_name = "edit_member.html"
    form_class = forms.MemberForm
    extra_context = {"types": MemberType.objects.all()}
    required_permission = "LedenAdministratie.change_member"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Make the form read-only when user has no change permissions
        if not self.request.user.has_perm("LedenAdministratie.change_member"):
            for _, field in form.fields.items():
                field.widget.attrs["disabled"] = True
        return form

    def get_success_url(self):
        return reverse("members")


class MemberCreateView(OTPRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Member
    template_name = "edit_member.html"
    success_url = reverse_lazy("members")
    form_class = forms.MemberForm
    extra_context = {"types": MemberType.objects.all()}
    required_permission = "LedenAdministratie.add_member"

    def form_valid(self, form):
        # Save form first
        redirect = super().form_valid(form)

        # Send 'welcome' e-mail to new member + parents
        recipients = form.cleaned_data["email_ouders"].split(",")
        recipients.append(form.cleaned_data["email_address"])

        message = EmailMessage()
        message.to = recipients
        message.subject = "Welkom bij DJO Amersfoort!"
        message.from_email = settings.EMAIL_SENDER
        message.body = render_to_string(
            "emails/welcome_email.html", context={"member": form.instance}
        )
        message.content_subtype = "html"

        response = requests.get(Utils.get_setting("welcome_pdf_location"), timeout=10)
        if response.ok:
            message.attach("Welkom bij DJO Amersfoort.pdf", response.content)
            Utils.send_email(message)

        return redirect


class MemberDeleteView(OTPRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Member
    success_url = reverse_lazy("members")
    template_name = "delete_member.html"
    fields = ["fist_name", "last_name"]
    extra_context = {"types": MemberType.objects.all()}
    required_permission = "LedenAdministratie.delete_member"


class MemberAddNoteView(OTPRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Note
    form_class = forms.LidNoteForm
    template_name = "member_note.html"
    required_permission = "LedenAdministratie.add_note"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["member"] = Member.objects.get(pk=self.kwargs["member_id"])
        return context

    def get_success_url(self):
        return reverse("lid_edit", kwargs={"pk": self.kwargs["member_id"]})

    def form_valid(self, form):
        member_id = self.kwargs["member_id"]
        form.instance.member = Member.objects.get(pk=member_id)
        form.instance.username = self.request.user.first_name
        return super().form_valid(form)


class MemberDeleteNoteView(OTPRequiredMixin, PermissionRequiredMixin, View):
    required_permission = "LedenAdministratie.delete_note"

    def get(self, request, *args, **kwargs):
        note = Note.objects.get(pk=kwargs["pk"])
        note.delete()
        return HttpResponseRedirect(Utils.get_safe_return_url(request))


class MemberEditNoteView(OTPRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Note
    form_class = forms.LidNoteForm
    template_name = "member_note.html"
    required_permission = "LedenAdministratie.change_note"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["member"] = self.object.member
        return context

    def get_success_url(self):
        return reverse("lid_edit", kwargs={"pk": self.object.member.id})


class TodoListView(OTPRequiredMixin, PermissionRequiredMixin, ListView):
    model = Note
    template_name = "todo_list.html"
    required_permission = "LedenAdministratie.view_note"

    def get_queryset(self):
        todos = Note.objects.filter(done=False)
        self.extra_context = {"types": MemberType.objects.all()}
        return todos


class InvoiceCreateView(OTPRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = "invoice_create.html"
    form_class = forms.InvoiceCreateForm
    LinesFormSet = formset_factory(forms.InvoiceLineForm, extra=5)
    lines: LinesFormSet = None
    invoice_type: InvoiceType = None
    refresh_only = False
    required_permission = "LedenAdministratie.add_invoice"

    def get_success_url(self):
        if self.kwargs.get("member_id"):
            url = reverse("lid_edit", kwargs={"pk": self.kwargs.get("member_id")})
        else:
            url = reverse("members")
        return url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["types"] = MemberType.objects.all()

        if self.kwargs.get("member_id"):
            context["member"] = Member.objects.get(pk=self.kwargs["member_id"])
        else:
            context["form"].fields[
                "members"
            ].queryset = InvoiceTool.get_members_invoice_type(self.invoice_type)

        self.lines = self.LinesFormSet(
            initial=InvoiceTool.get_defaults_for_invoice_type(
                self.invoice_type, context.get("member", None)
            )
        )
        context["invoice_lines"] = self.lines

        return context

    def post(self, request, *args, **kwargs):
        self.lines = self.LinesFormSet(request.POST, request.FILES)
        if "create" in request.POST:
            return super().post(request, *args, *kwargs)

        # Invoice type dropdown changed
        self.invoice_type = InvoiceType(request.POST["invoice_types"])
        form = self.get_form()
        form.errors.clear()
        return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, form: forms.InvoiceCreateForm):
        self.lines.is_valid()
        invoice_lines = [InvoiceLine(**line.cleaned_data) for line in self.lines]
        invoice_type = InvoiceType(form.cleaned_data["invoice_types"])
        for member in form.cleaned_data["members"]:
            InvoiceTool.create_invoice(
                invoice_type, member, invoice_lines, self.request.user.first_name
            )
        return super().form_valid(form)


class InvoiceDisplayView(OTPRequiredMixin, PermissionRequiredMixin, BaseDetailView):
    model = Invoice
    required_permission = "LedenAdministratie.view_invoice"

    def get(self, request, *args, **kwargs):
        invoice = self.get_object()
        return HttpResponse(invoice.pdf, content_type="application/pdf")


class InvoiceDeleteView(OTPRequiredMixin, PermissionRequiredMixin, View):
    required_permission = "LedenAdministratie.delete_invoice"

    def get(self, request, *args, **kwargs):
        invoice = Invoice.objects.get(pk=kwargs["pk"])
        invoice.delete()
        return HttpResponseRedirect(Utils.get_safe_return_url(request))


class InvoicePaymentView(OTPRequiredMixin, PermissionRequiredMixin, ListView):
    model = Invoice
    queryset = Invoice.objects.filter(amount_payed__lt=F("amount")).filter(
        member__isnull=False
    )
    template_name = "invoice_payment.html"
    extra_context = {"types": MemberType.objects.all()}
    required_permission = "LedenAdministratie.view_invoice"


class InvoicePayFullView(OTPRequiredMixin, PermissionRequiredMixin, View):
    required_permission = "LedenAdministratie.view_invoice"

    def get(self, request, *args, **kwargs):
        invoice = Invoice.objects.get(pk=kwargs["pk"])
        invoice.amount_payed = invoice.amount
        invoice.save()
        return HttpResponseRedirect(reverse("invoice_payment"))


class InvoicePayPartView(OTPRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Invoice
    template_name = "invoice_partial_payment.html"
    form_class = forms.InvoicePartialPaymentForm
    required_permission = "LedenAdministratie.view_invoice"

    def get_success_url(self):
        if self.kwargs.get("member_id"):
            return reverse("lid_edit", kwargs={"pk": self.kwargs["member_id"]})
        return reverse("invoice_payment")


class InvoiceSendView(OTPRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = "invoice_send.html"
    required_permission = "LedenAdministratie.view_invoice"
    form_class = forms.InvoiceSelectionForm
    success_url = reverse_lazy("invoice_send")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["types"] = MemberType.objects.all()
        context["object_list"] = Invoice.objects.filter(
            amount_payed__lt=F("amount")
        ).filter(member__isnull=False)
        return context

    def form_valid(self, form):
        invoices = form.cleaned_data["invoices"]
        is_reminder = "reminder" in self.request.POST
        for invoice in invoices:
            try:
                count = InvoiceTool.send_by_email(invoice, is_reminder)
                if count == 1:
                    invoice.sent = timezone.now()
                    invoice.smtp_error = None
                else:
                    invoice.smtp_error = "Fout bij versturen!"
            except Exception as e:  # pylint: disable=broad-exception-caught
                invoice.smtp_error = f"Fout bij versturen: {e}"

            invoice.save()
        return super().form_valid(form)


class ExportView(OTPRequiredMixin, PermissionRequiredMixin, FormView):
    form_class = forms.ExportForm
    template_name = "export.html"
    required_permission = "LedenAdministratie.view_member"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["types"] = MemberType.objects.all()
        return context

    def form_valid(self, form):
        filter_slug = "all"
        if form.cleaned_data["filter_slug"]:
            filter_slug = form.cleaned_data["filter_slug"].slug

        members = Member.objects.filter(
            Q(afmeld_datum__gt=timezone.now()) | Q(afmeld_datum=None)
        )
        if filter_slug != "all":
            members = members.filter(types__slug=filter_slug)

        filename = filter_slug + ".csv"
        response = HttpResponse(content_type="text/csv", charset="utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        writer = csv.writer(response, dialect=csv.excel, quoting=csv.QUOTE_ALL)
        writer.writerow(
            [
                "Voornaam",
                "Achternaam",
                "Geb. Datum",
                "Leeftijd",
                "Geslacht",
                "E-mail",
                "Straat",
                "Postcode",
                "Woonplaats",
                "Telnr",
                "Telnr Ouders",
                "E-mail Ouders",
            ]
        )

        for member in members:
            writer.writerow(
                [
                    member.first_name,
                    member.last_name,
                    member.gebdat,
                    member.age,
                    member.geslacht,
                    member.email_address,
                    member.straat,
                    member.postcode,
                    member.woonplaats,
                    member.telnr,
                    member.telnr_ouders,
                    member.email_ouders,
                ]
            )

        return response


class EmailSendView(OTPRequiredMixin, PermissionRequiredMixin, FormView):
    form_class = forms.EmailSendForm
    template_name = "email_send.html"
    required_permission = "LedenAdministratie.add_member"
    extra_context = {"types": MemberType.objects.all()}

    def send_email(self, form, recipients):
        if len(recipients) == 0:
            return None

        message = EmailMessage()
        message.from_email = settings.EMAIL_SENDER
        if form.cleaned_data["reply_to"] == "personal":
            message.reply_to = [self.request.user.email]
        elif form.cleaned_data["reply_to"] == "lanparty":
            message.reply_to = [settings.EMAIL_LANPARTY]
        message.to = recipients
        message.subject = form.cleaned_data["subject"]
        message.body = "<html>" + form.cleaned_data["body"] + "</html>"
        message.content_subtype = "html"

        if "attachment" in form.files:
            attachment = form.files["attachment"]
            content = b""
            for chunk in attachment.chunks():
                content += chunk
            message.attach(attachment.name, content)

        return Utils.send_email(message)

    def send_notification(self, form, recipients):
        if len(recipients) == 0:
            return
        if not settings.NOTIFICATION_ENDPOINT:
            return

        requests.post(
            settings.NOTIFICATION_ENDPOINT,
            json={
                "title": form.cleaned_data["subject"],
                "description": form.cleaned_data["description"],
                "content": form.cleaned_data["body"],
                "recipients": recipients,
            },
            timeout=10,
        )

    def form_valid(self, form):
        if "self" in form.cleaned_data["recipients"]:
            self.send_email(form, [self.request.user.email])

        recipients = Member.objects.filter(
            Q(afmeld_datum__gt=date.today()) | Q(afmeld_datum=None)
        )
        to_user_list = []
        for recipient in recipients:
            to_list = []
            if recipient.is_begeleider() or recipient.is_aspirant():
                if "begeleiders" in form.cleaned_data["recipients"]:
                    to_list.append(recipient.email_address)
                    to_user_list.append(str(recipient.user.id))
            elif recipient.is_ondersteuner():
                if "ondersteuning" in form.cleaned_data["recipients"]:
                    to_list.append(recipient.email_address)
                    to_user_list.append(str(recipient.user.id))
            else:
                if "parents" in form.cleaned_data["recipients"]:
                    for address in recipient.email_ouders.split(","):
                        to_list.append(address)
                if "members" in form.cleaned_data["recipients"]:
                    to_list.append(recipient.email_address)
                    to_user_list.append(str(recipient.user.id))

            self.send_email(form, to_list)
        self.send_notification(form, list(set(to_user_list)))

        return HttpResponseRedirect(reverse_lazy("email_log"))


class EmailLogView(OTPRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 100
    model = MessageLog
    queryset = MessageLog.objects.all().order_by("-when_added")
    template_name = "email_list.html"
    extra_context = {"types": MemberType.objects.all()}
    required_permission = "mailer.view_messagelog"


class SettingsView(OTPRequiredMixin, PermissionRequiredMixin, FormView):
    form_class = forms.SettingsForm
    template_name = "settings.html"
    extra_context = {
        "settings": Setting.objects.all(),
        "types": MemberType.objects.all(),
    }
    success_url = reverse_lazy("members")
    required_permission = "LedenAdministratie.view_setting"

    def get_initial(self):
        initial = super().get_initial()
        for setting in Setting.objects.all():
            initial[setting.name] = setting.value
        return initial

    def form_valid(self, form):
        for field in form.fields:
            try:
                setting = Setting.objects.get(name=field)
            except Setting.DoesNotExist:
                setting = Setting()
                setting.name = field
            setting.value = form.cleaned_data[field]
            setting.save()
        return super().form_valid(form)


class StripcardCreateView(OTPRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Stripcard
    template_name = "stripcard_create.html"
    form_class = forms.StripcardForm
    required_permission = "LedenAdministratie.add_stripcard"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["member"] = Member.objects.get(pk=self.kwargs["member_id"])
        return context

    def get_success_url(self):
        return reverse("lid_edit", kwargs={"pk": self.kwargs["member_id"]})

    def form_valid(self, form: forms.StripcardForm):
        member_id = self.kwargs["member_id"]
        form.instance.member = Member.objects.get(pk=member_id)
        form.instance.issued_by = self.request.user.first_name

        if form.cleaned_data["create_invoice"]:
            defaults = InvoiceTool.get_defaults_for_invoice_type(InvoiceType.STRIPCARD)[
                0
            ]
            defaults["count"] = form.cleaned_data["count"]
            line = InvoiceLine(**defaults)
            InvoiceTool.create_invoice(
                InvoiceType.STRIPCARD,
                form.instance.member,
                [line],
                self.request.user.first_name,
            )

        return super().form_valid(form)


class StripcardDeleteView(OTPRequiredMixin, PermissionRequiredMixin, View):
    required_permission = "LedenAdministratie.delete_stripcard"

    def get(self, request, *args, **kwargs):
        stripcard = Stripcard.objects.get(pk=kwargs["pk"])
        stripcard.delete()
        return HttpResponseRedirect(Utils.get_safe_return_url(request))
