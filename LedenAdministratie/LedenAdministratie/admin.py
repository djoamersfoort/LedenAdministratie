from django.contrib import admin
from. import models

admin.site.register(models.Member)
admin.site.register(models.MemberType)
admin.site.register(models.Invoice)
admin.site.register(models.Note)
