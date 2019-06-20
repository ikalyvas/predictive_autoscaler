import os
import time
import logging

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Metric
from .serializers import MetricSerializer
from .predictor_utils import Arima, HoltWinters, InvalidPredictorModelError


logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s]  %(message)s",
                    handlers=[
                        logging.FileHandler("{0}.log".format("predictor")),
                        logging.StreamHandler()
                    ])

logger = logging.getLogger('predictor')


@api_view(["GET", ])
def metrics(request):

    metrics = Metric.objects.all()
    serializer = MetricSerializer(metrics, many=True)
    return Response({"metrics": serializer.data, "status": status.HTTP_200_OK})


@api_view(["POST", ])
def predict(request):

    serializer = MetricSerializer(data=request.data)
    serializer.is_valid(True)
    metric = serializer.save()

    num_of_metrics = Metric.objects.filter(ns_id=metric.ns_id, vnf_member_index=metric.vnf_member_index).\
        values("ns_id", "vnf_member_index", "cooldown_period", "scaling_group_descriptor", "vdu_count", "cpu_load")
    logger.info(f"Found {len(num_of_metrics)} metrics for ns_id:{metric.ns_id}/vnf_member_index:{metric.vnf_member_index}")

    pr_model = get_predictor_model()
    logger.info(f"Using {pr_model.__name__} for prediction")

    cpu_load = [metric["cpu_load"] for metric in num_of_metrics]

    # now reverse the metric queryset so that we take the latest by timestamp values
    num_of_metrics.reverse()
    vdu_count = [metric["vdu_count"] for metric in num_of_metrics][0]
    ns_id = num_of_metrics[0]["ns_id"]
    scaling_group_descriptor = num_of_metrics[0]["scaling_group_descriptor"]
    cooldown_period = num_of_metrics[0]["cooldown_period"]
    vnf_member_index = num_of_metrics[0]["vnf_member_index"]
    data = {"cpu_load": cpu_load,
            "ns_id": ns_id,
            "vdu_count": vdu_count,
            "scaling_group_descriptor": scaling_group_descriptor,
            "cooldown_period": cooldown_period,
            "vnf_member_index": vnf_member_index
            }
    scale_num_of_ops, scale_direction = pr_model().predict(data)

    # TODO: need to predict here and do scale or not

    msg = f"{scale_direction} by {scale_num_of_ops}" if scale_direction else "No scaling operation was triggered"
    return Response(data={"msg": msg,
                          "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                          },
                    status=status.HTTP_201_CREATED)


def get_predictor_model():
    predictor_model = os.environ.get("PREDICTOR_MODEL", "ARIMA")
    if predictor_model == "ARIMA":
        return Arima
    elif predictor_model == "HOLTWINTERS":
        return HoltWinters
    else:
        raise InvalidPredictorModelError("Invalid model for prediction")

d={"ns_id":"a1","cpu_load":1.45352,"vdu_count":2,"scaling_group_descriptor":"vnf_autoscale","vnf_member_index":1,"cooldown_period":3}
