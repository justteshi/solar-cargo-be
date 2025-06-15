from django.contrib import admin
from .models import DeliveryReport, DeliveryReportImage, Item, DeliveryReportItem
from django.utils.html import format_html
from django.urls import reverse


class DeliveryReportImageInline(admin.TabularInline):
    model = DeliveryReportImage
    extra = 0


class DeliveryReportItemInline(admin.TabularInline):
    model = DeliveryReportItem
    extra = 0
    autocomplete_fields = ['item']
    fields = ['item', 'quantity']
    show_change_link = True


@admin.register(DeliveryReport)
class DeliveryReportAdmin(admin.ModelAdmin):
    inlines = [DeliveryReportImageInline, DeliveryReportItemInline]
    list_display = (
        'deliveryreport_link',
        'delivery_slip_number',
        'location',
        'checking_company',
        'supplier',
        'created_at'
    )
    search_fields = ('delivery_slip_number', 'location', 'supplier')
    list_filter = ('created_at', 'checking_company', 'logistic_company')

    @admin.display(description='DeliveryReport ID')
    def deliveryreport_link(self, obj):
        url = reverse('admin:reports_deliveryreport_change', args=[obj.id])
        return format_html('<a href="{}">Delivery Report {}</a>', url, obj.id)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name']
