import logging
import os

import requests
from statsmodels.tsa.arima_model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.holtwinters import SimpleExpSmoothing
from collections import namedtuple
import time
import bisect
import csv

from arima.settings import TRAINING_PHASE_DELAY, \
    DEFAULT_GRANULARITY, \
    NBI_AUTHENTICATION_URL, \
    LOGIN_DATA, \
    NBI_SOCKET_ADDR, \
    COOLDOWN

from typing import List, Optional

Metrics = namedtuple("Metrics", ["CPU_LOAD", "TIMESTAMP", "VDU_COUNT", "NS_ID", "VNF_MEMBER_INDEX"])

cpu_load_to_vdus = [Metrics(60 * y, "", y, "", "") for y in range(20)]


# [(0, 0), 60, 1), (120, 2), (180, 3), (240, 4), (300, 5), (360, 6), (420, 7), (480, 8), \
# (540, 9), (600, 10),(660, 11), (720, 12),(780, 13),(840, 14), (900, 15), (960, 16), (1020, 17), (1080, 18), (1140, 19)]


class Predictor(object):

    def __init__(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s]  %(message)s",
            handlers=[
                logging.FileHandler("{0}.log".format("predictor")),
                logging.StreamHandler()
            ])

        self.log = logging.getLogger('predictor')

    def predict_arima(self) -> Optional[None]:

        self.log.info(f"Waiting {TRAINING_PHASE_DELAY}s for gathering some historical data from Prometheus")
        time.sleep(TRAINING_PHASE_DELAY)
        self.log.info(f"Start predicting")

        while True:
            data = self.get_data()
            cpu_load = [item.CPU_LOAD for item in data]
            vdu_count = [item.VDU_COUNT for item in data]
            ns_id = [item.NS_ID for item in data]
            vnf_member_index = [item.VNF_MEMBER_INDEX for item in data]
            latest_vdu_count = vdu_count[-1]

            if cpu_load:
                self.log.info(f"Will train with {len(cpu_load)} values")
                model = ARIMA(cpu_load, order=(1, 1, 0))
                model_fit = model.fit(disp=False)
                # make prediction
                predicted_value = model_fit.forecast()[0][0]
                self.log.info(f"Predict that the next value will be {predicted_value}")
                index = bisect.bisect_left(cpu_load_to_vdus, (predicted_value,))
                needed_vdus_for_predicted_value = cpu_load_to_vdus[index].VDU_COUNT
                self.log.info(
                    f"Predicted cpu load is {predicted_value}.Need {needed_vdus_for_predicted_value} for this cpu load.")

                if needed_vdus_for_predicted_value > latest_vdu_count:  # need scale out
                    num_of_vdus_for_scale_out = needed_vdus_for_predicted_value - latest_vdu_count
                    self.scale_out(num_of_vdus_for_scale_out, ns_id[-1], vnf_member_index[-1])

                elif needed_vdus_for_predicted_value < latest_vdu_count:  # need scale in
                    num_of_vdus_for_scale_in = latest_vdu_count - needed_vdus_for_predicted_value
                    self.scale_in(num_of_vdus_for_scale_in, ns_id[-1], vnf_member_index[-1])

                else:
                    self.log.info(
                        f"Needed vdus are {needed_vdus_for_predicted_value}. Current vdus are {latest_vdu_count}.No action.")

                time.sleep(DEFAULT_GRANULARITY)

    def scale_out(self, num: int, ns_id: str, vnf_member_index: str) -> Optional[None]:

        token = self.get_authentication_token()

        headers = {
            'Accept': "application/json",
            'Content-Type': "application/yaml",
            'Authorization': 'Bearer {token}'.format(token=token)
        }
        self.log.warning(f"Scale out operation triggered.Will scale by {num}")
        body = {"scaleType": "SCALE_VNF",
                "scaleVnfData": {"scaleVnfType": "SCALE_OUT",
                                 "scaleByStepData":
                                     {"scaling-group-descriptor": "vnf_autoscale",
                                      "member-vnf-index": vnf_member_index}}}

        url = NBI_SOCKET_ADDR + "/osm/nslcm/v1/ns_instances/" + ns_id + "/scale"

        if num:
            for i in range(num):
                response = requests.post(url, headers=headers, json=body, verify=False)
                if response.status_code != 201:
                    self.log.error(f"Could not send scale out to LCM.{response.status_code}/{response.text}")
                else:
                    self.log.info(
                        f"SCALE_OUT operation sent to LCM at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
                time.sleep(COOLDOWN)

        else:
            self.log.warning(f"({num}) is insufficient for scaling out.Cannot scale by {num}")

    def scale_in(self, num: int, ns_id: str, vnf_member_index: str) -> Optional[None]:

        token = self.get_authentication_token()

        headers = {
            'Accept': "application/json",
            'Content-Type': "application/yaml",
            'Authorization': 'Bearer {token}'.format(token=token)
        }
        self.log.warning(f"Scale in operation triggered.Will scale by {num}")
        body = {"scaleType": "SCALE_VNF",
                "scaleVnfData": {"scaleVnfType": "SCALE_IN",
                                 "scaleByStepData":
                                     {"scaling-group-descriptor": "vnf_autoscale",
                                      "member-vnf-index": vnf_member_index}}}

        url = NBI_SOCKET_ADDR + "/osm/nslcm/v1/ns_instances/" + ns_id + "/scale"

        if num:
            for i in range(num):
                response = requests.post(url, headers=headers, json=body, verify=False)
                if response.status_code != 201:
                    self.log.error(f"Could not send scale in to LCM.{response.status_code}/{response.text}")
                else:
                    self.log.info(
                        f"SCALE_IN operation sent to LCM at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
                time.sleep(COOLDOWN)

        else:
            self.log.warning(f"({num}) is insufficient for scaling in.Cannot scale by {num}")

    def get_authentication_token(self) -> str:
        """
        :return: token to be used in subsequent requests to NBI API
        """
        headers = {
            'Accept': "application/json",
            'Content-Type': "application/yaml"
        }

        response = requests.post(NBI_AUTHENTICATION_URL,
                                 json=LOGIN_DATA,
                                 headers=headers,
                                 verify=False)
        json_resp = response.json()
        token = json_resp["id"]
        self.log.info(f"Got token {token}")
        return token

    def get_data(self) -> List[Metrics]:
        data = []
        fieldnames = ["ID", "NS_ID", "VNF_MEMBER_INDEX", "TIMESTAMP", "CPU_LOAD", "VDU_COUNT"]
        METRICS_FILE = os.environ.get("METRICS_FILE")
        with open(METRICS_FILE, newline='') as metrics_file:
            reader = csv.DictReader(metrics_file, fieldnames=fieldnames)
            header = next(reader)
            for row in reader:
                metric = Metrics(float(row["CPU_LOAD"]), float(row["TIMESTAMP"]), int(row["VDU_COUNT"]), row["NS_ID"],
                                 row["VNF_MEMBER_INDEX"])
                data.append(metric)
        return data


if __name__ == '__main__':
    p = Predictor()
    p.predict_arima()
