from django import forms
from django.contrib import admin
from .models import DeliveryReport, DeliveryReportImage, Item, DeliveryReportItem, DeliveryReportDamageImage, Location, Supplier
from django.utils.html import format_html
from django.urls import reverse
from django.core.exceptions import ValidationError

class NoExtraButtonsAdmin(admin.ModelAdmin):
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        # Hide "Save and add another" and "Save and continue editing"
        extra_context['show_save_and_add_another'] = False
        extra_context['show_save_and_continue'] = False
        return super().changeform_view(request, object_id, form_url, extra_context=extra_context)


class DeliveryReportAdminForm(forms.ModelForm):
    class Meta:
        model = DeliveryReport
        fields = '__all__'
        labels = {
            'supplier_fk': 'Supplier',      # ← тук сменяш лейбъла
        }

class ItemAdminForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = '__all__'

    def clean_location(self):
        location = self.cleaned_data.get('location')
        if not location:
            raise ValidationError("You must assign a Location to this Item.")
        return location


class ReadOnlyItemInline(admin.TabularInline):
    model = Item
    extra = 0
    can_delete = False
    readonly_fields = ['name']
    show_change_link = True  # Adds a link to the full Item edit page
    verbose_name_plural = 'Items available for this location'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

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
class DeliveryReportAdmin(NoExtraButtonsAdmin):
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
class ItemAdmin(NoExtraButtonsAdmin):
    form = ItemAdminForm
    search_fields = ['name']
    list_display = ['name', 'location']
    list_filter = ['location']

@admin.register(Supplier)
class SupplierAdmin(NoExtraButtonsAdmin):
    search_fields = ['name']   # autocomplete ще търси по това поле
    list_display = ['name']

@admin.register(Location)
class LocationAdmin(NoExtraButtonsAdmin):
    inlines = [ReadOnlyItemInline]
    search_fields = ['name']   # трябва, защото го ползваме в autocomplete_fields
    list_display = ['name']
