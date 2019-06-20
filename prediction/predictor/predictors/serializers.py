from rest_framework.serializers import ModelSerializer
from .models import Metric


class MetricSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Metric
