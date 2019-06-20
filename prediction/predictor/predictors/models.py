from django.db import models

# Create your models here.


class Results(models.Model):
    pass


class Metric(models.Model):
    ns_id = models.CharField(max_length=150)
    vnf_member_index = models.IntegerField()
    scaling_group_descriptor = models.CharField(max_length=150)
    cooldown_period = models.FloatField()
    vdu_count = models.IntegerField()
    cpu_load = models.FloatField()
    timestamp = models.DateTimeField()

    class Meta:
        ordering = ["timestamp", ]