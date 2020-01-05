from django.db import models

# Create your models here.


class Results(models.Model):
    pass


class Metric(models.Model):
    FR_CH = (('Β5Μ', 'B5M'), ('B10M', 'B10M'), ('B15M', 'B15M'), ('B20M', 'B20M'))
    ns_id = models.CharField(max_length=150)
    vnf_member_index = models.CharField(max_length=5)
    scaling_group_descriptor = models.CharField(max_length=150)
    vdu_count = models.IntegerField()
    cpu_load = models.FloatField()
    frequency = models.CharField(max_length=10, choices=FR_CH, default='B5M')
    fr_list = models.FileField(max_length=100, null=True, upload_to="uploaded_files")
    send_mail = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["timestamp", ]