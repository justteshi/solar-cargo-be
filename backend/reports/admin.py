from django.contrib import admin
from .models import DeliveryReport

@admin.register(DeliveryReport)
class DeliveryReportAdmin(admin.ModelAdmin):
    list_display = ('delivery_slip_number', 'location', 'checking_company', 'supplier', 'created_at')
    search_fields = ('delivery_slip_number', 'location', 'supplier')
    list_filter = ('created_at', 'checking_company', 'logistic_company')