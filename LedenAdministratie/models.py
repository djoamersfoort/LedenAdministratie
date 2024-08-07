import uuid
from datetime import date, datetime
from io import BytesIO

from PIL import Image
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.validators import RegexValidator, EmailValidator
from django.db import models
from django.db.models import F
from django.utils import timezone


class MemberType(models.Model):
    slug = models.SlugField()
    display_name = models.CharField(max_length=100)

    def __str__(self):
        return self.display_name


class Member(models.Model):
    class Meta:
        ordering = ["first_name", "last_name"]
        verbose_name_plural = "Leden"
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["first_name"]),
        ]

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if self.thumbnail is None and self.foto is not None:
            try:
                with BytesIO(self.foto) as f:
                    with Image.open(f, "r") as photo:
                        img_format = photo.format
                        thumbnail = photo.copy()
                        thumbnail.thumbnail((100, 150), Image.Resampling.LANCZOS)
                        thumbnail.format = img_format
                        encoded_thumb = BytesIO()
                        thumbnail.save(encoded_thumb, img_format)
                        self.thumbnail = encoded_thumb.getvalue()
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"Warning: thumbnail creation failed: {e}")

        if self.user is None:
            # Create new linked User
            self.user = get_user_model()()
            # Can't set an 'unusable_password' here, because it disables password resets
            self.user.password = make_password(str(uuid.uuid4()))
            self.user.username = self.email_address.lower()
            self.user.save()

        super().save(
            force_insert, force_update, using=using, update_fields=update_fields
        )

        # Update user fields
        self.user.first_name = self.first_name
        self.user.last_name = self.last_name
        self.user.username = self.email_address.lower()
        self.user.email = self.email_address
        self.user.is_active = self.is_active()
        self.user.save()

    def _calculate_age(self, on_date=date.today()) -> int:
        today = on_date
        born = self.gebdat
        return (
            # pylint: disable=no-member
            today.year
            - born.year
            - ((today.month, today.day) < (born.month, born.day))
        )

    @property
    def active_stripcard(self) -> "Stripcard":
        return self.stripcards.filter(used__lt=F("count")).first()

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def get_types_display(self) -> str:
        return ",".join([tmptype.display_name for tmptype in self.types.all()])

    def idp_types(self) -> str:
        result = []
        for membertype in self.types.all():
            name = membertype.slug
            if name == "member":
                name = "lid"
            elif name == "aspirant":
                name = "aspirant_begeleider"
            result.append(name)
        return ",".join(result)

    def is_bestuur(self) -> bool:
        slugs = [membertype.slug for membertype in self.types.all()]
        return "bestuur" in slugs

    def is_begeleider(self) -> bool:
        slugs = [membertype.slug for membertype in self.types.all()]
        return "begeleider" in slugs

    def is_ondersteuner(self) -> bool:
        slugs = [membertype.slug for membertype in self.types.all()]
        return "ondersteuning" in slugs

    def is_aspirant(self) -> bool:
        slugs = [membertype.slug for membertype in self.types.all()]
        return "aspirant" in slugs

    def is_senior(self) -> bool:
        slugs = [membertype.slug for membertype in self.types.all()]
        return "senior" in slugs

    def is_stripcard(self) -> bool:
        slugs = [membertype.slug for membertype in self.types.all()]
        return "strippenkaart" in slugs

    def is_standard(self) -> bool:
        slugs = [membertype.slug for membertype in self.types.all()]
        return "member" in slugs

    def is_active(self) -> bool:
        return self.afmeld_datum is None or self.afmeld_datum > timezone.now().date()

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )
    first_name = models.CharField(max_length=40)
    last_name = models.CharField(max_length=200)
    gebdat = models.DateField(verbose_name="Geboorte Datum")
    geslacht = models.CharField(
        max_length=1,
        choices=(("m", "Man"), ("v", "Vrouw"), ("o", "Anders")),
        blank=False,
        null=False,
        default="m",
    )
    types = models.ManyToManyField(MemberType)
    email_address = models.EmailField(
        max_length=200, validators=[EmailValidator(message="E-mail adres is ongeldig")]
    )
    straat = models.CharField(max_length=255)
    postcode = models.CharField(
        max_length=7,
        validators=[
            RegexValidator(
                regex=r"\d\d\d\d\s?[A-Za-z]{2}", message="De postcode is ongeldig"
            )
        ],
    )
    woonplaats = models.CharField(max_length=100)
    telnr = models.CharField(max_length=30, blank=True)
    telnr_ouders = models.CharField(max_length=30, blank=False)
    email_ouders = models.CharField(max_length=200, blank=False)
    aanmeld_datum = models.DateField(verbose_name="Aanmeld datum", auto_now=False)
    afmeld_datum = models.DateField(verbose_name="Afmeld datum", null=True, blank=True)
    days = models.IntegerField(
        verbose_name="Aantal dagdelen aanwezig",
        choices=((1, "1 dagdeel"), (2, "2 dagdelen")),
        default=1,
    )
    foto = models.BinaryField(blank=True, null=True, verbose_name="Foto", editable=True)
    thumbnail = models.BinaryField(
        blank=True, null=True, verbose_name="Thumbnail", editable=True
    )
    hoe_gevonden = models.CharField(max_length=255, blank=True, null=False, default="")
    revbank_account = models.CharField(
        max_length=255, blank=True, null=False, default=""
    )
    age = property(_calculate_age)


class Note(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="notes")
    created = models.DateField(auto_now_add=True, auto_now=False)
    username = models.CharField(max_length=255, null=False, default="")
    done = models.BooleanField(verbose_name="Afgerond", null=False, default=False)
    text = models.TextField(max_length=65535, null=False, default="")


class Invoice(models.Model):
    @property
    def invoice_number(self):
        return f"F1{self.member.id:0>4}-{self.pk:0>5}"

    @property
    def old_invoice_number(self):
        return f"F0{self.member.id:0>4}-{self.pk:0>5}"

    @property
    def payed(self):
        return self.amount == self.amount_payed

    @property
    def amount_unpaid(self):
        return self.amount - self.amount_payed

    member = models.ForeignKey(
        Member, on_delete=models.SET_NULL, related_name="invoices", null=True
    )
    created = models.DateField(auto_now_add=True, auto_now=False)
    username = models.CharField(max_length=255, null=False, default="")
    sent = models.DateTimeField(blank=True, null=True)
    smtp_error = models.CharField(max_length=4096, null=True, blank=True)
    amount = models.DecimalField(
        verbose_name="Bedrag", blank=False, default=0.00, decimal_places=2, max_digits=6
    )
    amount_payed = models.DecimalField(
        verbose_name="Bedrag Betaald",
        blank=False,
        default=0.00,
        decimal_places=2,
        max_digits=6,
    )
    pdf = models.BinaryField(blank=True, null=True, editable=True)

    def __str__(self):
        member_name = (
            f"{self.member.first_name} {self.member.last_name}" if self.member else ""
        )
        return f"Factuur: Door {self.username} voor {member_name}, bedrag {self.amount}, betaald {self.amount_payed}"


class Setting(models.Model):
    name = models.CharField(blank=False, null=False, max_length=50)
    value = models.CharField(blank=True, null=True, max_length=1024)

    def __str__(self):
        return f"{self.name} = {self.value}"


class Stripcard(models.Model):
    member = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="stripcards"
    )
    issue_date = models.DateField(verbose_name="Datum van uitgifte", auto_created=True)
    issued_by = models.CharField(
        verbose_name="Uitgegeven door", max_length=255, null=False, default=""
    )
    count = models.IntegerField(verbose_name="Aantal", default=10)
    used = models.IntegerField(verbose_name="Gebruikt", default=0)
    expiration_date = models.DateField(
        verbose_name="Vervaldatum", default=datetime(year=2099, month=1, day=1)
    )

    def __str__(self):
        member_name = (
            f"{self.member.first_name} {self.member.last_name}" if self.member else ""
        )
        return f"Strippenkaart: Door {self.issued_by}, voor {member_name}, voor {self.count} keer"
