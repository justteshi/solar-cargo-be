from django.contrib import admin
from .models import DeliveryReport, DeliveryReportImage, Item
from django.utils.html import format_html
from django.urls import reverse

def duplicate_delivery_report(modeladmin, request, queryset):
    for obj in queryset:
        obj.pk = None  # Clear the primary key to create a new instance
        obj.save()

duplicate_delivery_report.short_description = "Duplicate selected Delivery Reports"

class ItemInline(admin.TabularInline):  # or admin.StackedInline for vertical layout
    model = Item
    extra = 0  # number of empty forms shown
    fields = ('name', 'quantity')

class DeliveryReportImageInline(admin.TabularInline):
    model = DeliveryReportImage
    extra = 0

@admin.register(DeliveryReport)
class DeliveryReportAdmin(admin.ModelAdmin):
    inlines = [DeliveryReportImageInline, ItemInline]
    list_display = ('deliveryreport_link', 'delivery_slip_number', 'location', 'checking_company', 'supplier', 'created_at')
    search_fields = ('delivery_slip_number', 'location', 'supplier')
    list_filter = ('created_at', 'checking_company', 'logistic_company')
    actions = [duplicate_delivery_report]

    @admin.display(description='DeliveryReport ID')
    def deliveryreport_link(self, obj):
        url = reverse('admin:reports_deliveryreport_change', args=[obj.id])
        return format_html('<a href="{}">Delivery Report {}</a>', url, obj.id)