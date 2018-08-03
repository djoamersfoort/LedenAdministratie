from django.db import models
from datetime import date
from django.core.validators import RegexValidator, EmailValidator


class LidManager(models.Manager):
    def proper_lastname_order(self, *args, **kwargs):
        qs = self.get_queryset().filter(*args, **kwargs)
        return sorted(qs, key=lambda n: n.last_name.lower().split()[-1])


class Lid(models.Model):
    objects = LidManager()
    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name_plural = "Leden"
        permissions = (
            ('read_lid', 'Can read leden'),
        )

    LIJST_CHOICES=[
        ('nieuw', 'Nieuw'),
        ('leden', 'Leden'),
        ('begeleiding', 'Begeleiding'),
        ('bestuur', 'Bestuur'),
    ]

    def _calculate_age(self, ondate = date.today()):
        today = ondate
        born = self.gebdat
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    def __str__(self):
        return "%s %s" % (self.first_name, self.last_name)

    first_name = models.CharField(max_length=40)
    last_name = models.CharField(max_length=200)
    gebdat = models.DateField(verbose_name='Geboorte Datum')
    geslacht = models.CharField(max_length=1, choices=(('m', 'M'),('v','V')), blank=False, null=False, default='m')
    speltak = models.CharField(max_length=40, choices=LIJST_CHOICES, default='nieuw', blank=False, null=False)
    email_address = models.EmailField(max_length=150, validators=[EmailValidator(message='E-mail adres is ongeldig')])
    straat = models.CharField(max_length=255)
    postcode = models.CharField(max_length=7, validators=[RegexValidator(regex='\d\d\d\d\s?[A-Za-z]{2}', message='De postcode is ongeldig')])
    woonplaats = models.CharField(max_length=100)
    telnr = models.CharField(max_length=30)
    mobiel = models.CharField(max_length=20, blank=True, validators=[RegexValidator(regex='06.*', message='Mobiel nummer is ongeldig')])
    mobiel_ouder1 = models.CharField(max_length=20, blank=True, validators=[RegexValidator(regex='06.*', message='Mobiel nummer is ongeldig')])
    mobiel_ouder2 = models.CharField(max_length=20, blank=True, validators=[RegexValidator(regex='06.*', message='Mobiel nummer is ongeldig')])
    email_ouder1 = models.EmailField(max_length=150, blank=True)
    email_ouder2 = models.EmailField(max_length=150, blank=True)
    aanmeld_datum = models.DateField(auto_now_add=True, auto_now=False)
    opmerkingen = models.TextField(max_length=1024, blank=True)
    age = property(_calculate_age)
