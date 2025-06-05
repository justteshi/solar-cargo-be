from django.contrib import admin
from .models import DeliveryReport, DeliveryReportImage
from django.utils.html import format_html
from django.urls import reverse

class DeliveryReportImageInline(admin.TabularInline):
    model = DeliveryReportImage
    extra = 1

@admin.register(DeliveryReport)
class DeliveryReportAdmin(admin.ModelAdmin):
    inlines = [DeliveryReportImageInline]
    list_display = ('deliveryreport_link', 'delivery_slip_number', 'location', 'checking_company', 'supplier', 'created_at')
    search_fields = ('delivery_slip_number', 'location', 'supplier')
    list_filter = ('created_at', 'checking_company', 'logistic_company')

    @admin.display(description='DeliveryReport ID')
    def deliveryreport_link(self, obj):
        url = reverse('admin:reports_deliveryreport_change', args=[obj.id])
        return format_html('<a href="{}">Delivery Report {}</a>', url, obj.id)