import abc
import logging
import os

import requests
from collections import namedtuple
import time
import bisect
from typing import Optional, Union, Tuple, Any
import numpy as np

from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima_model import ARIMA

from django.conf import settings

Metrics = namedtuple("Metrics", ["CPU_LOAD", "TIMESTAMP", "VDU_COUNT", "NS_ID", "VNF_MEMBER_INDEX"])

cpu_load_to_vdus = [Metrics(60 * y, "", y, "", "") for y in range(20)]


# [(0, 0), 60, 1), (120, 2), (180, 3), (240, 4), (300, 5), (360, 6), (420, 7), (480, 8), \
# (540, 9), (600, 10),(660, 11), (720, 12),(780, 13),(840, 14), (900, 15), (960, 16), (1020, 17), (1080, 18), (1140, 19)]


class Predictor(object):
    TRAINING_PHASE_DELAY = eval(os.environ.get("TRAINING_PHASE_DELAY"))
    DEFAULT_GRANULARITY = int(os.environ.get("DEFAULT_GRANULARITY"))
    NBI_AUTHENTICATION_URL = os.environ.get("NBI_AUTHENTICATION_URL")
    NBI_SOCKET_ADDR = os.environ.get("NBI_SOCKET_ADDR")

    # COOLDOWN = int(os.environ.get("COOLDOWN"))

    def __init__(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s]  %(message)s",
            handlers=[
                logging.FileHandler("{0}.log".format("predictor")),
                logging.StreamHandler()
            ])

        self.log = logging.getLogger('predictor')

    def scale(self, direction: str, num: int, ns_id: str, vnf_member_index: str,
              scaling_group_descriptor: str, cooldown_period: int) -> None:

        token = self.get_authentication_token()

        headers = {
            'Accept': "application/json",
            'Content-Type': "application/yaml",
            'Authorization': 'Bearer {token}'.format(token=token)
        }

        if direction == "SCALE_OUT":
            self.log.warning(f"Scale out operation triggered.Will scale by {num}")
        else:
            self.log.warning(f"Scale in operation triggered.Will scale by {num}")

        body = {"scaleType": "SCALE_VNF",
                "scaleVnfData": {"scaleVnfType": direction,
                                 "scaleByStepData":
                                     {"scaling-group-descriptor": scaling_group_descriptor,
                                      "member-vnf-index": vnf_member_index}}}

        url = self.NBI_SOCKET_ADDR + "/osm/nslcm/v1/ns_instances/" + ns_id + "/scale"

        if num:
            for i in range(num):
                response = requests.post(url, headers=headers, json=body, verify=False)
                if response.status_code != 201:
                    raise ScaleOperationError(
                        f"Could not send {direction} to LCM.{response.status_code}/{response.text}")
                else:
                    self.log.info(
                        f"{direction} operation sent to LCM at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
                time.sleep(cooldown_period)

        else:
            self.log.warning(f"({num}) is insufficient for {direction}.Cannot scale by {num}")

    def get_authentication_token(self) -> str:
        """
        :return: token to be used in subsequent requests to NBI API
        """
        headers = {
            'Accept': "application/json",
            'Content-Type': "application/yaml"
        }

        response = requests.post(self.NBI_AUTHENTICATION_URL,
                                 json=settings.LOGIN_DATA,
                                 headers=headers,
                                 verify=False)
        json_resp = response.json()
        token = json_resp["id"]
        self.log.info(f"Got token {token}")
        return token

    @abc.abstractmethod
    def predict(self, data) -> Union[Tuple[int, str], Tuple[Any, Any]]:
        raise NotImplementedError


class HoltWinters(Predictor):

    def predict(self, data) -> Union[Tuple[int, str], Tuple[Any, Any]]:

        direction = ""
        self.log.info(f"Start predicting with Holt-Winters")

        cpu_load = data.get("cpu_load")
        latest_vdu_count = data.get("vdu_count")
        ns_id = data.get("ns_id")
        vnf_member_index = data.get("vnf_member_index")
        scaling_group_descriptor = data.get("scaling_group_descriptor")
        cooldown_period = data.get("cooldown_period")

        self.log.info(f"Will train with {len(cpu_load)} values")
        model = ExponentialSmoothing(cpu_load, trend='additive')
        model_fit = model.fit()
        # make prediction
        predicted_value = model_fit.forecast()[0]
        self.log.info(f"Predict that the next value will be {predicted_value}")
        index = bisect.bisect_left(cpu_load_to_vdus, (predicted_value,))
        needed_vdus_for_predicted_value = cpu_load_to_vdus[index].VDU_COUNT
        self.log.info(
            f"Predicted cpu load is {predicted_value}."
            f"Need {needed_vdus_for_predicted_value} for this cpu load."
            f"Current number of VDUs is {latest_vdu_count}")

        if needed_vdus_for_predicted_value > latest_vdu_count:  # need scale out
            num_of_vdus_for_scale_out = needed_vdus_for_predicted_value - latest_vdu_count
            direction = "SCALE_OUT"
            self.scale(direction, num_of_vdus_for_scale_out, ns_id, vnf_member_index, scaling_group_descriptor,
                       cooldown_period)

        elif needed_vdus_for_predicted_value < latest_vdu_count:  # need scale in
            num_of_vdus_for_scale_in = latest_vdu_count - needed_vdus_for_predicted_value
            direction = "SCALE_IN"
            self.scale(direction, num_of_vdus_for_scale_in, ns_id, vnf_member_index, scaling_group_descriptor,
                       cooldown_period)

        else:
            self.log.info(
                f"Needed vdus are {needed_vdus_for_predicted_value}. Current vdus are {latest_vdu_count}.No action.")

        return abs(needed_vdus_for_predicted_value - latest_vdu_count), direction


class Arima(Predictor):

    def predict(self, data) -> Union[Tuple[int, str], Tuple[Any, Any]]:

        direction = ""
        self.log.info(f"Start predicting with Arima")

        cpu_load = data.get("cpu_load")
        latest_vdu_count = data.get("vdu_count")
        ns_id = data.get("ns_id")
        vnf_member_index = data.get("vnf_member_index")
        scaling_group_descriptor = data.get("scaling_group_descriptor")
        cooldown_period = data.get("cooldown_period")

        self.log.info(f"Will train with {len(cpu_load)} values")
        try:
            model = ARIMA(cpu_load, order=(1, 1, 0))
            model_fit = model.fit(disp=False)
        except np.linalg.LinAlgError:
            assert len(set(cpu_load)) == 1, "cpu_load values are not all the same!!!"
            self.log.exception("Singular matrix detected.All metric values must be the same.Adding noise to overcome")
            model = ARIMA(cpu_load + 0.00001 * np.random.rand(1, len(cpu_load))[0], order=(1, 1, 0))
            model_fit = model.fit(disp=False)

        except ValueError:
            self.log.exception("Insufficient degrees of operation.Retry when the values are more than 4.")
            return None, None
        # make prediction
        predicted_value = model_fit.forecast()[0][0]
        self.log.info(f"Predict that the next value will be {predicted_value}")
        index = bisect.bisect_left(cpu_load_to_vdus, (predicted_value,))
        needed_vdus_for_predicted_value = cpu_load_to_vdus[index].VDU_COUNT
        self.log.info(
            f"Predicted cpu load is {predicted_value}."
            f"Need {needed_vdus_for_predicted_value} for this cpu load."
            f"Current number of VDUs is {latest_vdu_count}")

        if needed_vdus_for_predicted_value > latest_vdu_count:  # need scale out
            num_of_vdus_for_scale_out = needed_vdus_for_predicted_value - latest_vdu_count
            direction = "SCALE_OUT"
            self.scale(direction, num_of_vdus_for_scale_out, ns_id, vnf_member_index, scaling_group_descriptor,
                       cooldown_period)

        elif needed_vdus_for_predicted_value < latest_vdu_count:  # need scale in
            num_of_vdus_for_scale_in = latest_vdu_count - needed_vdus_for_predicted_value
            direction = "SCALE_IN"
            self.scale(direction, num_of_vdus_for_scale_in, ns_id, vnf_member_index, scaling_group_descriptor,
                       cooldown_period)

        else:
            self.log.info(
                f"Needed vdus are {needed_vdus_for_predicted_value}. Current vdus are {latest_vdu_count}.No action.")

        return abs(needed_vdus_for_predicted_value - latest_vdu_count), direction


class InvalidPredictorModelError(Exception):
    pass


class ScaleOperationError(Exception):
    pass
