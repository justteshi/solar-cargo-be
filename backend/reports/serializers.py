from rest_framework import serializers
from .models import DeliveryReport, Item
import json

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['name', 'quantity']

class DeliveryReportSerializer(serializers.ModelSerializer):
    items_input = serializers.CharField(write_only=True, required=False, help_text='JSON array of items to create.')
    items = ItemSerializer(many=True, read_only=True)

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

    class Meta:
        model = DeliveryReport
        fields = [
            'items_input',
            # Основни данни:
            'location',
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
            'comments',
            'items',
            # Стъпка 3:
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

            'user',
        ]

    # includes image_1, image_2, created_at, etc.

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

        # Правило: Трябва да има или табела на камион или снимка
        truck_plate = data.get('licence_plate_truck')
        truck_image = data.get('truck_license_plate_image')
        if not truck_plate and not truck_image:
            raise serializers.ValidationError({
                'licence_plate_truck': "Provide either the truck license plate number or the truck license plate image."
            })

        # Правило: Трябва да има или табела на ремарке или снимка
        trailer_plate = data.get('licence_plate_trailer')
        trailer_image = data.get('trailer_license_plate_image')
        if not trailer_plate and not trailer_image:
            raise serializers.ValidationError({
                'licence_plate_trailer': "Provide either the trailer license plate number or the trailer license plate image."
            })

        # Правило: Ако създаваме нов, items_input не трябва да липсва
        if self.context['request'].method == 'POST':
            if 'items_input' not in self.initial_data:
                raise serializers.ValidationError({
                    'items_input': "This field is required when creating a DeliveryReport."
                })

        return data

    def create(self, validated_data):
        items_data = validated_data.pop('items_input', [])
        report = DeliveryReport.objects.create(**validated_data)
        for item in items_data:
            Item.objects.create(delivery_report=report, **item)
        return report