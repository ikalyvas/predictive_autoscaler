import abc
import logging
import os
import pickle
import time
import bisect
from typing import Union, Tuple, Any
from collections import namedtuple

import requests
import numpy as np
from django.conf import settings
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima_model import ARIMA
import tensorflow as tf


Metrics = namedtuple("Metrics", ["CPU_LOAD", "TIMESTAMP", "VDU_COUNT", "NS_ID", "VNF_MEMBER_INDEX"])

cpu_load_to_vdus = [Metrics(60 * y, "", y, "", "") for y in range(30)]

lstm_model = pickle.load(open(os.path.join('predictor/predictors/trained_models', 'lstm_model.sav'), 'rb'))
graph = tf.get_default_graph()

log = logging.getLogger(__name__)


class Predictor(object):
    """
    Base class for the various predictor implementations (ARIMA, HOLTWINTER, LSTM-RNN)
    """

    NBI_AUTHENTICATION_URL = os.environ.get("NBI_AUTHENTICATION_URL")
    NBI_SOCKET_ADDR = os.environ.get("NBI_SOCKET_ADDR")

  

    @classmethod
    def scale(cls, direction: str, num: int, ns_id: str, vnf_member_index: str,
              scaling_group_descriptor: str) -> None:

        """
        Main scale function which uses the LCM endpoint to send the scale out / scale in requests upon decision.
        :param direction:
        :param num:
        :param ns_id:
        :param vnf_member_index:
        :param scaling_group_descriptor:
        :return:
        """


        token = cls.get_authentication_token()

        headers = {
            'Accept': "application/json",
            'Content-Type': "application/yaml",
            'Authorization': 'Bearer {token}'.format(token=token)
        }

        if direction == "SCALE_OUT":
            log.warning(f"Scale out operation triggered.Will scale by {num}")
        else:
            log.warning(f"Scale in operation triggered.Will scale by {num}")

        body = {"scaleType": "SCALE_VNF",
                "scaleVnfData": {"scaleVnfType": direction,
                                 "scaleByStepData":
                                     {"scaling-group-descriptor": scaling_group_descriptor,
                                      "member-vnf-index": vnf_member_index}}}

        url = cls.NBI_SOCKET_ADDR + "/osm/nslcm/v1/ns_instances/" + ns_id + "/scale"

        if num:
            for i in range(num):
                response = requests.post(url, headers=headers, json=body, verify=False)
                if response.status_code != 201:
                    raise ScaleOperationError(
                        f"Could not send {direction} to LCM.{response.status_code}/{response.text}")
                else:
                    log.info(
                        f"{direction} operation sent to LCM at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
                time.sleep(1)

        else:
            log.warning(f"({num}) is insufficient for {direction}.Cannot scale by {num}")

    @classmethod
    def get_authentication_token(cls) -> str:
        """
        :return: token to be used in subsequent requests to NBI API
        """
        headers = {
            'Accept': "application/json",
            'Content-Type': "application/yaml"
        }

        response = requests.post(cls.NBI_AUTHENTICATION_URL,
                                 json=settings.LOGIN_DATA,
                                 headers=headers,
                                 verify=False)
        json_resp = response.json()
        token = json_resp["id"]
        log.info(f"Got token {token}")
        return token

    @abc.abstractmethod
    def predict(self, data) -> Union[Tuple[int, str], Tuple[Any, Any]]:
        """
        Abstract base method for prediction.Implemented in child classes
        :param data:
        :return:
        """
        raise NotImplementedError

    @classmethod
    def scale_decision(cls, needed_vdus, latest_vdus, ns_id, vnf_member_index, scaling_group_descriptor):

        """
        Method that contains the logic for triggering any scale operation.It uses the total cpu load for all of the VMs that are posted by the metric collector
        and acts accordingly in order to decide if scale is needed.
        :param needed_vdus:
        :param latest_vdus:
        :param ns_id:
        :param vnf_member_index:
        :param scaling_group_descriptor:
        :return:
        """

        if needed_vdus > latest_vdus:  # need scale out
            num_of_vdus_for_scale_out = needed_vdus - latest_vdus
            direction = "SCALE_OUT"
            cls.scale(direction, num_of_vdus_for_scale_out, ns_id, vnf_member_index, scaling_group_descriptor)

        elif needed_vdus < latest_vdus:  # need scale in
            num_of_vdus_for_scale_in = latest_vdus - needed_vdus
            direction = "SCALE_IN"
            cls.scale(direction, num_of_vdus_for_scale_in, ns_id, vnf_member_index, scaling_group_descriptor)
        else:
            log.info(
                f"Needed vdus are {needed_vdus}. Current vdus are {latest_vdus}.No action.")


class HoltWinters(Predictor):

    @classmethod
    def predict(cls, data) -> Union[Tuple[int, str], Tuple[Any, Any]]:
        """
        HoltWinters implementation
        :param data:
        :return:
        """

        direction = ""
        log.info(f"Start predicting with Holt-Winters")

        cpu_load = data.get("cpu_load")
        latest_vdu_count = data.get("vdu_count")
        ns_id = data.get("ns_id")
        vnf_member_index = data.get("vnf_member_index")
        scaling_group_descriptor = data.get("scaling_group_descriptor")

        log.info(f"Will train with {len(cpu_load)} values")
        model = ExponentialSmoothing(cpu_load, trend='additive')
        model_fit = model.fit()
        # make prediction
        predicted_value = model_fit.forecast()[0]
        log.info(f"Predict that the next value will be {predicted_value}")
        index = bisect.bisect_left(cpu_load_to_vdus, (predicted_value,))
        needed_vdus_for_predicted_value = cpu_load_to_vdus[index].VDU_COUNT
        log.info(
            f"Predicted cpu load is {predicted_value}."
            f"Need {needed_vdus_for_predicted_value} for this cpu load."
            f"Current number of VDUs is {latest_vdu_count}")
        cls.scale_decision(needed_vdus_for_predicted_value, latest_vdu_count, ns_id, vnf_member_index,
                            scaling_group_descriptor)

        return abs(needed_vdus_for_predicted_value - latest_vdu_count), direction


class Arima(Predictor):

    @classmethod
    def predict(cls, data) -> Union[Tuple[int, str], Tuple[Any, Any]]:

        """
        ARIMA implementation
        :param data:
        :return:
        """

        direction = ""
        log.info(f"Start predicting with Arima")

        cpu_load = data.get("cpu_load")
        latest_vdu_count = data.get("vdu_count")
        ns_id = data.get("ns_id")
        vnf_member_index = data.get("vnf_member_index")
        scaling_group_descriptor = data.get("scaling_group_descriptor")

        log.info(f"Will train with {len(cpu_load)} values")
        try:
            model = ARIMA(cpu_load, order=(1, 1, 0))
            model_fit = model.fit(disp=False)
        except np.linalg.LinAlgError:
            assert len(set(cpu_load)) == 1, "cpu_load values are not all the same!!!"
            log.exception("Singular matrix detected.All metric values must be the same.Adding noise to overcome")
            model = ARIMA(cpu_load + 0.00001 * np.random.rand(1, len(cpu_load))[0], order=(1, 1, 0))
            model_fit = model.fit(disp=False)

        except ValueError:
            log.exception("Insufficient degrees of operation.Retry when the values are more than 4.")
            return None, None
        # make prediction
        predicted_value = model_fit.forecast()[0][0]
        log.info(f"Predict that the next value will be {predicted_value}")
        index = bisect.bisect_left(cpu_load_to_vdus, (predicted_value,))
        needed_vdus_for_predicted_value = cpu_load_to_vdus[index].VDU_COUNT
        log.info(
            f"Predicted cpu load is {predicted_value}."
            f"Need {needed_vdus_for_predicted_value} for this cpu load."
            f"Current number of VDUs is {latest_vdu_count}")

        cls.scale_decision(needed_vdus_for_predicted_value, latest_vdu_count, ns_id, vnf_member_index,
                            scaling_group_descriptor)

        return abs(needed_vdus_for_predicted_value - latest_vdu_count), direction


class Lstm(Predictor):

    @classmethod
    def predict(cls, data) -> Union[Tuple[int, str], Tuple[Any, Any]]:

        """
        Long Short-Term Memory (Recurrent Neural Networks) implementation
        :param data:
        :return:
        """

        n_features = 1 # univariate variable
        num_of_steps = 3 # need to take if from env?

        direction = ""
        log.info(f"Start predicting with RNN (Long Short-Term Memory)")

        # use the latest num_of_steps values as input to do the prediction
        if len(data.get("cpu_load")) >= num_of_steps:
            cpu_load = data.get("cpu_load")[-num_of_steps:]
        else:
            raise Exception(f"Cannot predict yet with LSTM as input data ({data.get('cpu_load')}) are less than {num_of_steps}")

        latest_vdu_count = data.get("vdu_count")
        ns_id = data.get("ns_id")
        vnf_member_index = data.get("vnf_member_index")
        scaling_group_descriptor = data.get("scaling_group_descriptor")

        log.info(f"Will predict with input {num_of_steps} values. Use {cpu_load}")

        # load the model

        cpu_load = np.array(cpu_load).reshape(1, num_of_steps, n_features)
        with graph.as_default():
            predicted_value = lstm_model.predict(cpu_load, verbose=0)[0]

        log.info(f"Predict that the next value will be {predicted_value}")
        index = bisect.bisect_left(cpu_load_to_vdus, (predicted_value,))
        needed_vdus_for_predicted_value = cpu_load_to_vdus[index].VDU_COUNT
        log.info(
            f"Predicted cpu load is {predicted_value}."
            f"Need {needed_vdus_for_predicted_value} for this cpu load."
            f"Current number of VDUs is {latest_vdu_count}")

        cls.scale_decision(needed_vdus_for_predicted_value, latest_vdu_count,
                            ns_id, vnf_member_index,
                            scaling_group_descriptor)

        return abs(needed_vdus_for_predicted_value - latest_vdu_count), direction


class InvalidPredictorModelError(Exception):
    pass


class ScaleOperationError(Exception):
    pass


def get_predictor_model():
    """
    Method that returns the model we want to use for prediction.Driven by an environment variable.
    :return:
    """

    predictor_model = os.environ.get("PREDICTOR_MODEL", "ARIMA")
    if predictor_model == "ARIMA":
        return Arima
    elif predictor_model == "HOLTWINTERS":
        return HoltWinters
    elif predictor_model == "LSTM":
        return Lstm
    else:
        raise InvalidPredictorModelError("Invalid model for prediction")
