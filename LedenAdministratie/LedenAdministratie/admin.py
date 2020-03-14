from django.contrib import admin
from. import models

admin.site.register(models.Member)
admin.site.register(models.MemberType)
admin.site.register(models.Invoice)
admin.site.register(models.Note)
admin.site.register(models.APIToken)
admin.site.register(models.Email)
admin.site.register(models.Setting)