from rest_framework import serializers
from .models import DeliveryReport

class DeliveryReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryReport
        fields = '__all__'