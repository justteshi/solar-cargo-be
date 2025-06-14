from rest_framework import serializers
from .models import DeliveryReport, Item
import json

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['name', 'quantity']

class DeliveryReportSerializer(serializers.ModelSerializer):
    # Accept JSON string on POST
    items_input = serializers.CharField(write_only=True, required=False, help_text='JSON array of items to create.')

    # Show nested items in responses
    items = ItemSerializer(many=True, read_only=True)

    class Meta:
        model = DeliveryReport
        fields = '__all__'  # includes image_1, image_2, created_at, etc.

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

    def create(self, validated_data):
        items_data = validated_data.pop('items_input', [])
        report = DeliveryReport.objects.create(**validated_data)
        for item in items_data:
            Item.objects.create(report=report, **item)
        return report