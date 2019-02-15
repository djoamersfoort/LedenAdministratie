from django.db import models
from datetime import date
from django.core.validators import RegexValidator, EmailValidator


class MemberType(models.Model):
    slug = models.SlugField()
    display_name = models.CharField(max_length=100)

    def __str__(self):
        return self.display_name


class MemberManager(models.Manager):
    def proper_lastname_order(self, *args, **kwargs):
        qs = self.get_queryset().filter(*args, **kwargs)
        return sorted(qs, key=lambda n: n.last_name.lower().split()[-1])


class Member(models.Model):
    objects = MemberManager()

    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name_plural = "Leden"
        permissions = (
            ('read_member', 'Can read members'),
        )

    def _calculate_age(self, ondate = date.today()):
        today = ondate
        born = self.gebdat
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    def get_types_display(self):
        return ','.join([tmptype.display_name for tmptype in self.types.all()])

    def __str__(self):
        return "%s %s" % (self.first_name, self.last_name)

    first_name = models.CharField(max_length=40)
    last_name = models.CharField(max_length=200)
    gebdat = models.DateField(verbose_name='Geboorte Datum')
    geslacht = models.CharField(max_length=1, choices=(('m', 'Man'), ('v', 'Vrouw'), ('o', 'Anders')), blank=False, null=False, default='m')
    types = models.ManyToManyField(MemberType)
    email_address = models.EmailField(max_length=200, validators=[EmailValidator(message='E-mail adres is ongeldig')])
    straat = models.CharField(max_length=255)
    postcode = models.CharField(max_length=7, validators=[RegexValidator(regex='\d\d\d\d\s?[A-Za-z]{2}', message='De postcode is ongeldig')])
    woonplaats = models.CharField(max_length=100)
    telnr = models.CharField(max_length=30)
    telnr_ouders = models.CharField(max_length=30, blank=True)
    email_ouders = models.EmailField(max_length=150, blank=True)
    aanmeld_datum = models.DateField(auto_now_add=True, auto_now=False)
    age = property(_calculate_age)


class Note(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='notes')
    created = models.DateField(auto_now_add=True, auto_now=False)
    username = models.CharField(max_length=255, null=False, default='')
    text = models.TextField(max_length=65535, null=False, default='')
