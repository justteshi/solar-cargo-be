from django import forms
from django.contrib import admin
from .models import DeliveryReport, DeliveryReportImage, Item, DeliveryReportItem, DeliveryReportDamageImage, Location, Supplier, DeliveryReportGSCProofImage
from django.utils.html import format_html
from django.urls import reverse
from django.core.exceptions import ValidationError
from .services import ReportFileService, ReportDataService, ReportUpdateService
from django.forms.models import BaseInlineFormSet

class GSCProofInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        count = 0
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            cd = form.cleaned_data
            if cd.get("DELETE"):
                continue
            # има файл или вече съществуващ обект
            if cd.get("image") or form.instance and form.instance.pk:
                count += 1

        if count < 1 or count > 3:
            raise ValidationError("Моля качете между 1 и 3 снимки за Goods/Seal/Container proof.")

class GSCProofInline(admin.TabularInline):
    model = DeliveryReportGSCProofImage
    formset = GSCProofInlineFormSet
    extra = 0
    fields = ("preview", "image", "uploaded_at")
    readonly_fields = ("preview", "uploaded_at")
    verbose_name_plural = "Goods / Seal / Container proof (1–3 снимки)"

    def preview(self, obj):
        if obj and getattr(obj, "image", None):
            try:
                return format_html('<img src="{}" style="max-height:100px;"/>', obj.image.url)
            except Exception:
                pass
        return "-"


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
    class Media:
        js = ('admin/js/delivery_report_loader.js',)

    form = DeliveryReportAdminForm
    inlines = [GSCProofInline,
       DeliveryReportImageInline,
       DeliveryReportItemInline,
       DeliveryReportDamageImageInline
    ]

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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        try:
            # Services for generating files
            file_service = ReportFileService()
            data_service = ReportDataService()
            update_service = ReportUpdateService()

            # Generate filenames and paths
            filenames = file_service.generate_filenames()
            excel_path = file_service.generate_excel_path(filenames['excel'])

            # Prepare report data (you might need to use a serializer or manually collect the data)
            from .serializers import DeliveryReportSerializer
            serializer = DeliveryReportSerializer(obj)
            prepared_data = data_service.prepare_report_data(serializer.data)

            # Generate files
            file_service.generate_files(prepared_data, excel_path)

            # Update file fields in DB
            update_service.update_report_files(
                obj.id,
                filenames['excel'],
                filenames['pdf']
            )
        except Exception as e:
            logger.error(f"Admin file generation failed for DeliveryReport {obj.id}: {e}")

    def _generate_files(self, instance):
        try:
            from .services import ReportFileService, ReportDataService, ReportUpdateService
            from .serializers import DeliveryReportSerializer

            file_service = ReportFileService()
            data_service = ReportDataService()
            update_service = ReportUpdateService()

            filenames = file_service.generate_filenames()
            excel_path = file_service.generate_excel_path(filenames['excel'])

            serializer = DeliveryReportSerializer(instance)
            prepared_data = data_service.prepare_report_data(serializer.data)

            file_service.generate_files(prepared_data, excel_path)

            update_service.update_report_files(
                instance.id, filenames['excel'], filenames['pdf']
            )
        except Exception as e:
            logger.error(f"Admin file generation failed for DeliveryReport {instance.id}: {e}")

    def save_model(self, request, obj, form, change):
        # запазва само родителя
        super().save_model(request, obj, form, change)
        # НЕ генерираме тук, защото инлайновете още не са запазени

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        instance = form.instance

        def do_generate():
            self._generate_files(instance)

        try:
            transaction.on_commit(do_generate)
        except Exception:
            # ако няма активна транзакция
            do_generate()


@admin.register(Item)
class ItemAdmin(NoExtraButtonsAdmin):
    form = ItemAdminForm
    search_fields = ['name']
    list_display = ['name', 'location']
    list_filter = ['location']

class SupplierAdminForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = '__all__'
        widgets = {
            'locations': forms.CheckboxSelectMultiple
        }

@admin.register(Supplier)
class SupplierAdmin(NoExtraButtonsAdmin):
    search_fields = ['name']
    list_display = ['name']
    autocomplete_fields = ['locations']
    list_filter = ['locations']

@admin.register(Location)
class LocationAdmin(NoExtraButtonsAdmin):
    inlines = [ReadOnlyItemInline]
    search_fields = ['name']
    list_display = ['name']
