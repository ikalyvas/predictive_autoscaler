from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from .models import Metric


class MetricSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Metric

# frequency = serializers.SerializerMethodField()

# def get_frequency(self, obj):
#     return obj.get_frequency_display()
