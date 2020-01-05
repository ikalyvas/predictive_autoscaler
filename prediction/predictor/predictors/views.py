import os
import time
import logging

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FileUploadParser
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Metric
from .serializers import MetricSerializer
from .predictor_utils import get_predictor_model
from .forms import MetricForm
logger = logging.getLogger(__name__)


class MetricsViewsSet(ModelViewSet):
    serializer_class = MetricSerializer
    queryset = Metric.objects.all()
    renderer_classes = [TemplateHTMLRenderer, ]
    template_name = "profile_list.html"

    def create(self, request, *args, **kwargs):

        form = MetricForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            metrics = self.get_queryset()
            return Response({"metrics": metrics}, status=status.HTTP_201_CREATED)
        else:
            return Response({"errors": form.errors})

    def list(self, request, *args, **kwargs):
        metrics = self.get_queryset()
        form = MetricForm()
        return Response({"form": form, "metrics": metrics})

    def retrieve(self, request, pk=None):
        p = get_object_or_404(Metric, pk=pk)
        s = MetricSerializer(p)
        return Response({'serializer': s, 'profile': p}, template_name='profile_get.html')

    @action(detail=False, methods=["DELETE", ])
    def delete_all(self, request):
        metrics_deleted = Metric.objects.all().delete()
        return Response(data=metrics_deleted[1], status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["POST", ])
    def filetest(self, request):
        base_location = settings.MEDIA_ROOT + '/'

        print(request.data.get('send_mail'))
        myfile = request.FILES['fr_list']
        fs = FileSystemStorage()
        if os.path.exists(base_location + myfile.name):
            print('Already uploadedH file with same name.')
        filename = fs.save(myfile.name, myfile)
        print(myfile)
        print(settings.MEDIA_ROOT + '/' + filename)
        assert os.path.exists(settings.MEDIA_ROOT + '/' + filename)
        # with open(settings.MEDIA_ROOT+'/'+ filename) as f:
        #    for line in f:
        #        print(line)
        return Response(data={}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["POST", ])
    def predict(self, request):
        serializer = MetricSerializer(data=request.data)
        serializer.is_valid(True)
        metric = serializer.save()

        num_of_metrics = Metric.objects.filter(ns_id=metric.ns_id, vnf_member_index=metric.vnf_member_index). \
            values("ns_id", "vnf_member_index", "scaling_group_descriptor", "vdu_count", "cpu_load")
        logger.info(
            f"Found {len(num_of_metrics)} metrics for ns_id:{metric.ns_id}/vnf_member_index:{metric.vnf_member_index}")

        pr_model = get_predictor_model()
        logger.info(f"Using {pr_model.__name__} for prediction")

        cpu_load = [metric["cpu_load"] for metric in num_of_metrics]

        # now reverse the metric queryset so that we take the latest by timestamp values
        reversed_num_of_metrics = num_of_metrics.reverse()
        vdu_count = [metric["vdu_count"] for metric in reversed_num_of_metrics][0]
        ns_id = reversed_num_of_metrics[0]["ns_id"]
        scaling_group_descriptor = reversed_num_of_metrics[0]["scaling_group_descriptor"]
        vnf_member_index = reversed_num_of_metrics[0]["vnf_member_index"]
        data = {"cpu_load": cpu_load,
                "ns_id": ns_id,
                "vdu_count": vdu_count,
                "scaling_group_descriptor": scaling_group_descriptor,
                "vnf_member_index": vnf_member_index
                }

        try:
            scale_num_of_ops, scale_direction = pr_model.predict(data)
        except Exception:
            logger.exception(f"Error while doing prediction.")
            return Response(data={"msg": "Error while doing prediction"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        msg = f"{scale_direction} by {scale_num_of_ops}" if scale_direction else "No scaling operation was triggered"
        return Response(data={"msg": msg,
                              "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),},
                        status=status.HTTP_201_CREATED)
