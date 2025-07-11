from rest_framework import serializers
from .models import DeliveryReport, Item, DeliveryReportItem, DeliveryReportImage, Location, DeliveryReportDamageImage, \
    DeliveryReportSlipImage
from drf_spectacular.utils import extend_schema_field
import json

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'logo']

# Delivery Report Item
class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'name']


class DeliveryReportItemSerializer(serializers.ModelSerializer):
    item = ItemSerializer()

    class Meta:
        model = DeliveryReportItem
        fields = ['item', 'quantity']

# End Delivery Report Item serializer

# Delivery Report Images Serializer
class DeliveryReportImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryReportImage
        fields = ['image', 'uploaded_at']
# End Delivery Report Images Serializer

# Serializer for damage images
class DeliveryReportDamageImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryReportDamageImage
        fields = ['image', 'uploaded_at']

class DeliveryReportSlipImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryReportSlipImage
        fields = ['image', 'uploaded_at']

class OptionalImageListField(serializers.ListField):
    child = serializers.ImageField()

    def to_internal_value(self, data):
        # if swagger/curl gave you "", None or a single file,
        # DRF might wrap them differently. Ensure you have a list:
        if not isinstance(data, list):
            return []

        # filter only file-like objects
        files = [f for f in data if hasattr(f, 'read')]
        if not files:
            # no real files → treat as empty
            return []

        # now validate the real files list
        return super().to_internal_value(files)

class DeliveryReportSerializer(serializers.ModelSerializer):
    items_input = serializers.CharField(
        write_only=True,
        required=False,
        help_text='JSON array of items to create.',
        default='[]',
    )
    items = serializers.SerializerMethodField(read_only=True)

    additional_images_input = OptionalImageListField(
    required=False,
    allow_null=True,
    allow_empty=True,
    write_only=True,
    help_text='List of additional image files.'
)
    additional_images_urls = DeliveryReportImageSerializer(source='additional_images', many=True, read_only=True)

    # other fields...
    load_secured_comment = serializers.CharField(required=False, allow_blank=True, allow_null=True, default=None)
    goods_according_comment = serializers.CharField(required=False, allow_blank=True, allow_null=True, default=None)
    packaging_comment = serializers.CharField(required=False, allow_blank=True, allow_null=True, default=None)
    delivery_without_damages_comment = serializers.CharField(required=False, allow_blank=True, allow_null=True,default=None)
    suitable_machines_comment = serializers.CharField(required=False, allow_blank=True, allow_null=True, default=None)
    delivery_slip_comment = serializers.CharField(required=False, allow_blank=True, allow_null=True, default=None)
    inspection_report_comment = serializers.CharField(required=False, allow_blank=True, allow_null=True, default=None)

    load_secured_status = serializers.BooleanField(required=False, allow_null=True)
    goods_according_status = serializers.BooleanField(required=False, allow_null=True)
    packaging_status = serializers.BooleanField(required=False, allow_null=True)
    delivery_without_damages_status = serializers.BooleanField(required=False, allow_null=True)
    suitable_machines_status = serializers.BooleanField(required=False, allow_null=True)
    delivery_slip_status = serializers.BooleanField(required=False, allow_null=True)
    inspection_report_status = serializers.BooleanField(required=False, allow_null=True)

    # Step 5: Damage section
    damage_description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        default=None,
        help_text='Damage description.'
    )
    damage_images_input = OptionalImageListField(
        required=False,
        allow_null=True,
        allow_empty=True,
        write_only=True,
        max_length=4,
        help_text='Up to 4 damage images.'
    )
    damage_images_urls = DeliveryReportDamageImageSerializer(
        source='damage_images',
        many=True,
        read_only=True
    )

    location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
    )

    location_name = serializers.CharField(
        source='location.name',
        read_only=True,
        help_text='Name of the assigned location'
    )

    delivery_slip_images_input = OptionalImageListField(
        child=serializers.ImageField(),
        write_only=True,
        required=True,
        allow_empty=False,
        help_text='At least one image file is required.'
    )
    delivery_slip_images_urls = DeliveryReportSlipImageSerializer(
        source='slip_images',
        many=True,
        read_only=True
    )

    class Meta:
        model = DeliveryReport
        fields = [
            # Step 1 report general info:
            'id',
            'location',
            'location_name',
            'checking_company',
            'supplier',
            'delivery_slip_number',
            'logistic_company',
            'container_number',
            'licence_plate_truck',
            'licence_plate_trailer',
            'truck_license_plate_image',
            'trailer_license_plate_image',
            'weather_conditions',
            'comments', # Bozhidar: this seems unnecessary, remove it
            # Step 2 report items:
            'items_input',
            'items',  # replaced with method field showing item + quantity
            'proof_of_delivery_image',
            # Step 3 checkboxes:
            'load_secured_status',
            'load_secured_comment',
            'goods_according_status',
            'goods_according_comment',
            'packaging_status',
            'packaging_comment',
            'delivery_without_damages_status',
            'delivery_without_damages_comment',
            'suitable_machines_status',
            'suitable_machines_comment',
            'delivery_slip_status',
            'delivery_slip_comment',
            'inspection_report_status',
            'inspection_report_comment',
            # Step 4 images:
            'cmr_image',
            'delivery_slip_images_input',
            'delivery_slip_images_urls',
            'additional_images_input',
            'additional_images_urls',
            'damage_description',
            'damage_images_input',
            'damage_images_urls',
            'user',
        ]

    def get_items(self, obj):
        # This returns a list of items with quantity
        report_items = DeliveryReportItem.objects.filter(delivery_report=obj)
        return DeliveryReportItemSerializer(report_items, many=True).data

    def validate_delivery_slip_images_input(self, files):
        if not files:
            raise serializers.ValidationError("At least one image file is required.")
        return files

    def validate_items_input(self, value):
        try:
            items_list = json.loads(value)
            if not isinstance(items_list, list):
                raise serializers.ValidationError("Must be a list.")
            for item in items_list:
                if not isinstance(item, dict):
                    raise serializers.ValidationError("Each item must be an object.")
                if "name" not in item or "quantity" not in item:
                    raise serializers.ValidationError("Each item must have 'name' and 'quantity'.")
                if not isinstance(item["quantity"], int) or item["quantity"] <= 0:
                    raise serializers.ValidationError("Quantity must be a positive integer.")
            return items_list
        except json.JSONDecodeError:
            raise serializers.ValidationError("Must be valid JSON.")

    def validate(self, data):
        comment_fields = [
            'load_secured_comment',
            'goods_according_comment',
            'packaging_comment',
            'delivery_without_damages_comment',
            'suitable_machines_comment',
            'delivery_slip_comment',
            'inspection_report_comment'
        ]
        for field in comment_fields:
            if field in data and data[field] == '':
                data[field] = None

        truck_plate = data.get('licence_plate_truck')
        truck_image = data.get('truck_license_plate_image')
        if not truck_plate and not truck_image:
            raise serializers.ValidationError({
                'licence_plate_truck': "Provide either the truck license plate number or the truck license plate image."
            })

        trailer_plate = data.get('licence_plate_trailer')
        trailer_image = data.get('trailer_license_plate_image')
        if not trailer_plate and not trailer_image:
            raise serializers.ValidationError({
                'licence_plate_trailer': "Provide either the trailer license plate number or the trailer license plate image."
            })
        proof_of_delivery = data.get('proof_of_delivery_image')
        if not proof_of_delivery:
            raise serializers.ValidationError({
                'proof_of_delivery': "Provide proof of delivery image."
            })

        cmr_image = data.get('cmr_image')
        if not cmr_image:
            raise serializers.ValidationError({
                'cmr_image': "Provide cmr image."
            })

        if self.context['request'].method == 'POST':
            if 'items_input' not in self.initial_data:
                raise serializers.ValidationError({
                    'items_input': "This field is required when creating a DeliveryReport."
                })

        return data

    def create(self, validated_data):
        # Pop items input JSON (list of dicts)
        items_data = validated_data.pop('items_input', [])
        # Pop additional images files list
        additional_images_files = validated_data.pop('additional_images_input', [])
        damage_images = validated_data.pop('damage_images_input', [])
        damage_desc = validated_data.get('damage_description', None)
        slips = validated_data.pop('delivery_slip_images_input', [])

        # Create DeliveryReport without extra fields
        report = super().create(validated_data)

        # Create related items
        for item in items_data:
            item_obj, _ = Item.objects.get_or_create(name=item['name'])
            DeliveryReportItem.objects.create(
                delivery_report=report,
                item=item_obj,
                quantity=item['quantity']
            )

        for img in slips:
            DeliveryReportSlipImage.objects.create(
                delivery_report=report,
                image=img
            )

        # Create DeliveryReportImage instances for additional images
        for uploaded_file in additional_images_files:
            DeliveryReportImage.objects.create(
                delivery_report=report,
                image=uploaded_file
            )

        # Process damage section
        if damage_desc:
            report.damage_description = damage_desc
            report.save()
        for img in damage_images:
            DeliveryReportDamageImage.objects.create(delivery_report=report, image=img)

        return report

class ItemAutocompleteFilterSerializer(serializers.Serializer):
    q = serializers.CharField(required=True, min_length=2, help_text="Search term for item name")
