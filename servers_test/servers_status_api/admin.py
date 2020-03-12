from django.contrib import admin
from .models import SeversHistory


# Register your models here.

class SeversHistoryAdmin(admin.ModelAdmin):
    readonly_fields = ('consultation_date',)


admin.site.register(SeversHistory, SeversHistoryAdmin)
