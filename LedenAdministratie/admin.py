from django.contrib import admin
from LedenAdministratie import models


class MemberAdmin(admin.ModelAdmin):
    exclude = ["foto", "thumbnail"]


class InvoiceAdmin(admin.ModelAdmin):
    exclude = ["pdf"]


admin.site.register(models.Member, MemberAdmin)
admin.site.register(models.MemberType)
admin.site.register(models.Invoice, InvoiceAdmin)
admin.site.register(models.Note)
admin.site.register(models.Setting)
