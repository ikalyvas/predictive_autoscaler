import time
import logging

from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Metric
from .serializers import MetricSerializer
from .predictor_utils import get_predictor_model

logger = logging.getLogger(__name__)


class MetricsViewsSet(ModelViewSet):
    serializer_class = MetricSerializer
    queryset = Metric.objects.all()

    @action(detail=False, methods=["DELETE", ])
    def delete_all(self, request):
        metrics_deleted = Metric.objects.all().delete()
        return Response(data=metrics_deleted[1], status=status.HTTP_204_NO_CONTENT)

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
