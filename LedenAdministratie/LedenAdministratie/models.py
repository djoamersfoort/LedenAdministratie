from django.db import models
from datetime import date
from django.core.validators import RegexValidator, EmailValidator
from PIL import Image
from io import BytesIO


class MemberType(models.Model):
    slug = models.SlugField()
    display_name = models.CharField(max_length=100)

    def __str__(self):
        return self.display_name


class Member(models.Model):

    class Meta:
        ordering = ["first_name", "last_name"]
        verbose_name_plural = "Leden"

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if self.thumbnail is None and self.foto is not None:
            try:
                with BytesIO(self.foto) as f:
                    with Image.open(f, "r") as photo:
                        img_format = photo.format
                        thumbnail = photo.copy()
                        thumbnail.thumbnail((100, 150), Image.LANCZOS)
                        thumbnail.format = img_format
                        encoded_thumb = BytesIO()
                        thumbnail.save(encoded_thumb, img_format)
                        self.thumbnail = encoded_thumb.getvalue()
            except Exception as e:
                print("Warning: thumbnail creation failed: {0}".format(str(e)))

        super().save(force_insert, force_update, using=using, update_fields=update_fields)

    def _calculate_age(self, ondate=date.today()):
        today = ondate
        born = self.gebdat
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    @property
    def full_name(self):
        return "{0} {1}".format(self.first_name, self.last_name)

    def get_types_display(self):
        return ','.join([tmptype.display_name for tmptype in self.types.all()])

    def idp_types(self):
        result = []
        for membertype in self.types.all():
            name = membertype.slug
            if name == 'member':
                name = 'lid'
            elif name == 'aspirant':
                name = 'aspirant_begeleider'
            result.append(name)
        return ','.join(result)

    def is_begeleider(self):
        slugs = [membertype.slug for membertype in self.types.all()]
        return 'begeleider' in slugs or 'aspirant' in slugs or 'ondersteuning' in slugs

    def __str__(self):
        return "%s %s" % (self.first_name, self.last_name)

    first_name = models.CharField(max_length=40)
    last_name = models.CharField(max_length=200)
    gebdat = models.DateField(verbose_name='Geboorte Datum')
    geslacht = models.CharField(max_length=1, choices=(('m', 'Man'), ('v', 'Vrouw'), ('o', 'Anders')), blank=False,
                                null=False, default='m')
    types = models.ManyToManyField(MemberType)
    email_address = models.EmailField(max_length=200, validators=[EmailValidator(message='E-mail adres is ongeldig')])
    straat = models.CharField(max_length=255)
    postcode = models.CharField(max_length=7, validators=[
        RegexValidator(regex='\d\d\d\d\s?[A-Za-z]{2}', message='De postcode is ongeldig')])
    woonplaats = models.CharField(max_length=100)
    telnr = models.CharField(max_length=30, blank=True)
    telnr_ouders = models.CharField(max_length=30, blank=False)
    email_ouders = models.CharField(max_length=200, blank=False)
    aanmeld_datum = models.DateField(verbose_name='Aanmeld datum', auto_now=False)
    afmeld_datum = models.DateField(verbose_name='Afmeld datum', null=True, blank=True)
    dag_vrijdag = models.BooleanField(null=False, default=False)
    dag_zaterdag = models.BooleanField(null=False, default=False)
    foto = models.BinaryField(blank=True, null=True, verbose_name='Foto', editable=True)
    thumbnail = models.BinaryField(blank=True, null=True, verbose_name='Thumbnail', editable=True)
    hoe_gevonden = models.CharField(max_length=255, blank=True, null=False, default='')
    age = property(_calculate_age)


class Note(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='notes')
    created = models.DateField(auto_now_add=True, auto_now=False)
    username = models.CharField(max_length=255, null=False, default='')
    done = models.BooleanField(verbose_name='Afgerond', null=False, default=False)
    text = models.TextField(max_length=65535, null=False, default='')


class Invoice(models.Model):

    @property
    def invoice_number(self):
        return 'F1{0:0>4}-{1:0>5}'.format(self.member.id, self.pk)

    @property
    def old_invoice_number(self):
        return 'F0{0:0>4}-{1:0>5}'.format(self.member.id, self.pk)

    @property
    def payed(self):
        return self.amount == self.amount_payed

    @property
    def amount_unpaid(self):
        return self.amount - self.amount_payed

    member = models.ForeignKey(Member, on_delete=models.SET_NULL, related_name='invoices', null=True)
    created = models.DateField(auto_now_add=True, auto_now=False)
    username = models.CharField(max_length=255, null=False, default='')
    sent = models.DateTimeField(blank=True, null=True)
    smtp_error = models.CharField(max_length=4096, null=True, blank=True)
    amount = models.DecimalField(verbose_name='Bedrag', blank=False, default=0.00, decimal_places=2, max_digits=6)
    amount_payed = models.DecimalField(verbose_name='Bedrag Betaald', blank=False, default=0.00, decimal_places=2,
                                       max_digits=6)
    pdf = models.BinaryField(blank=True, null=True, editable=True)


class APIToken(models.Model):
    token_type = models.CharField(max_length=12)
    token = models.CharField(max_length=64)
    expires = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "{0} - {1}".format(self.token_type, self.token)


class Email(models.Model):
    sent = models.DateTimeField(blank=True, null=True)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='emails', null=True)
    recipients = models.CharField(max_length=4096)
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=4096)
    sent_by = models.CharField(max_length=255, null=False, default='')


class Setting(models.Model):
    name = models.CharField(blank=False, null=False, max_length=50)
    value = models.CharField(blank=True, null=True, max_length=1024)

    def __str__(self):
        return "{0} = {1}".format(self.name, self.value)
