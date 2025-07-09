from django.contrib import admin
from .models import DeliveryReport, DeliveryReportImage, Item, DeliveryReportItem, DeliveryReportDamageImage
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

class DeliveryReportDamageImageInline(admin.TabularInline):
    model = DeliveryReportDamageImage
    extra = 0
    verbose_name = 'Damage Image'
    verbose_name_plural = 'Damage Images'

@admin.register(DeliveryReport)
class DeliveryReportAdmin(admin.ModelAdmin):
    inlines = [DeliveryReportImageInline, DeliveryReportItemInline, DeliveryReportDamageImageInline]
    list_display = (
        'deliveryreport_link',
        'delivery_slip_number',
        'location',
        'checking_company',
        'supplier',
        'damage_description',
        'created_at'
    )
    search_fields = ('delivery_slip_number', 'location', 'supplier')
    list_filter = ('created_at', 'checking_company', 'logistic_company')
    readonly_fields = ('excel_report_file', 'pdf_report_file', 'damage_description')

    @admin.display(description='DeliveryReport ID')
    def deliveryreport_link(self, obj):
        url = reverse('admin:reports_deliveryreport_change', args=[obj.id])
        return format_html('<a href="{}">Delivery Report {}</a>', url, obj.id)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name']

from .models import Location, LocationAssignment

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(LocationAssignment)
class LocationAssignmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'location']
    search_fields = ['user__email', 'location__name']
    autocomplete_fields = ['user', 'location']
