from django.forms import ModelForm, FileField
from .models import Metric


class MetricForm(ModelForm):
    fr_list = FileField(max_length=100, required=False)

    class Meta:
        model = Metric
        fields = "__all__"
