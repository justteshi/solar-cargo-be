from django import forms
from django.contrib import admin
from .models import DeliveryReport, DeliveryReportImage, Item, DeliveryReportItem, DeliveryReportDamageImage, Location, Supplier
from django.utils.html import format_html
from django.urls import reverse

class DeliveryReportAdminForm(forms.ModelForm):
    class Meta:
        model = DeliveryReport
        fields = '__all__'
        labels = {
            'supplier_fk': 'Supplier',      # ← тук сменяш лейбъла
        }

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
    form = DeliveryReportAdminForm
    inlines = [DeliveryReportImageInline, DeliveryReportItemInline, DeliveryReportDamageImageInline]

    exclude = ['supplier']
    autocomplete_fields = ['supplier_fk', 'location']

    list_display = (
        'deliveryreport_link',
        'delivery_slip_number',
        'location',
        'checking_company',
        'supplier_name',
        'supplier',
        'damage_description',
        'created_at'
    )
    search_fields = ('delivery_slip_number', 'location', 'supplier_fk__name',)
    list_filter = ('created_at', 'checking_company', 'logistic_company')
    readonly_fields = ('excel_report_file', 'pdf_report_file', 'damage_description')

    @admin.display(description='DeliveryReport ID')
    def deliveryreport_link(self, obj):
        url = reverse('admin:reports_deliveryreport_change', args=[obj.id])
        return format_html('<a href="{}">Delivery Report {}</a>', url, obj.id)

    @admin.display(description='Supplier')
    def supplier_name(self, obj):
        if obj.supplier_fk:
            return obj.supplier_fk.name
        return obj.supplier or '-'


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name']

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    search_fields = ['name']   # autocomplete ще търси по това поле
    list_display = ['name']

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    search_fields = ['name']   # трябва, защото го ползваме в autocomplete_fields
    list_display = ['name']
