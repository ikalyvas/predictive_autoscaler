import datetime
import logging
import time
from itertools import groupby
from collections import defaultdict
import os

import yaml
import requests


class ScalingDataMissingError(Exception):
    pass


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]  %(message)s",
    handlers=[
        logging.FileHandler("{0}.log".format("metrics_collector")),
        logging.StreamHandler()
    ])


class MetricCollector(object):

    def __init__(self):
        self.logger = logging.getLogger('metrics_manager.metrics_collector')
        self.ns_to_vnf_member_index = defaultdict(lambda: defaultdict(lambda: {}))
        self.prom_ip = os.environ.get("PROMETHEUS_IP")
        self.prom_port = os.environ.get("PROMETHEUS_PORT")
        self.prom_url = "http://" + self.prom_ip + ":" + self.prom_port + "/"
        self.granularity_interval = int(os.environ.get("DEFAULT_GRANULARITY"))
        self.NBI_AUTHENTICATION_URL = os.environ.get("NBI_AUTHENTICATION_URL")
        self.NBI_SOCKET_ADDR = os.environ.get("NBI_SOCKET_ADDR")
        self.VNFS_URL = self.NBI_SOCKET_ADDR + "/osm/nslcm/v1/vnf_instances?nsr-id-ref={ns_id}"
        self.VNFD_URL = self.NBI_SOCKET_ADDR + "/osm/vnfpkgm/v1/vnf_packages/{vnf_id}/vnfd"
        self.CPU_UTIL_METRIC_URL = self.prom_url + "api/v1/query?query=osm_cpu_utilization"
        self.login_data = {"username": "admin", "password": "admin"}
        self.authentication_token = self.get_authentication_token()

    @staticmethod
    def read_config(config, field):

        return yaml.load(open(config)).get("prometheus_config").get(field)

    def get_authentication_token(self) -> str:
        """
        :return: token to be used in subsequent requests to NBI API
        """
        headers = {
            'Accept': "application/json",
            'Content-Type': "application/yaml"
        }

        response = requests.post(self.NBI_AUTHENTICATION_URL,
                                 json=self.login_data,
                                 headers=headers,
                                 verify=False)
        json_resp = response.json()
        token = json_resp["id"]
        self.logger.info(f"Got token {token}")
        return token

    def process_metric(self, ns_id: str, vnf_member_index: int):
        """
        Given an ns_id and a vnf_member_index it returns the scaling_group_descriptor and the cooldown period
        of this particular ns_id---vnf_member_index group
        :return:
        """
        headers = {
            'Accept': "application/json",
            'Authorization': 'Bearer {token}'.format(token=self.authentication_token)
        }

        if ns_id in self.ns_to_vnf_member_index and str(vnf_member_index) in self.ns_to_vnf_member_index[ns_id]:
            self.logger.info(f"Using cache for accessing...")
            return (self.ns_to_vnf_member_index[ns_id][vnf_member_index]["cooldown_period"],
                    self.ns_to_vnf_member_index[ns_id][vnf_member_index]["scale_group_descriptor_name"])

        retry = 3
        while retry != 0:
            vnf_response = requests.get(self.VNFS_URL.format(ns_id=ns_id), verify=False, headers=headers)
            if vnf_response.status_code == 401:
                self.token = self.get_authentication_token()
                headers['Authorization'].format(token=self.token)
                retry -= 1
            elif vnf_response.status_code == 200:
                vnfs = vnf_response.json()
                self.logger.info(f"Found {len(vnfs)} VNFS for {ns_id}.Checking which VNF belongs to {vnf_member_index}")
                for vnf in vnfs:
                    vnfd_headers = {"Accept": "application/yaml,text/plain",
                                    'Authorization': 'Bearer {token}'.format(token=self.authentication_token)}
                    if vnf.get("member-vnf-index-ref") == vnf_member_index:
                        vnfd = vnf.get("vnfd-id")
                        vnfd_response = requests.get(self.VNFD_URL.format(vnf_id=vnfd), verify=False,
                                                     headers=vnfd_headers)
                        vnfd = yaml.load(vnfd_response.text)
                        scale_group_descriptor_name = \
                        vnfd["vnfd:vnfd-catalog"]["vnfd"][0]["scaling-group-descriptor"][0]["name"]
                        cooldown_period = \
                        vnfd["vnfd:vnfd-catalog"]["vnfd"][0]["scaling-group-descriptor"][0]["scaling-policy"][0][
                            "cooldown-time"]
                        self.ns_to_vnf_member_index[ns_id][vnf_member_index]["cooldown_period"] = cooldown_period
                        self.ns_to_vnf_member_index[ns_id][vnf_member_index][
                            "scale_group_descriptor_name"] = scale_group_descriptor_name

                        return (self.ns_to_vnf_member_index[ns_id][vnf_member_index]["cooldown_period"],
                                self.ns_to_vnf_member_index[ns_id][vnf_member_index]["scale_group_descriptor_name"])

                raise ScalingDataMissingError(
                    f"Cannot find scaling group descriptor for ns-id:{ns_id} and vnf_member_index:{vnf_member_index}")

    def get_cpu_load(self):

        while True:
            response = requests.get(self.CPU_UTIL_METRIC_URL)
            resp = response.json()
            results = resp.get("data").get("result")
            if results:
                self.logger.info(f"Got {len(results)} VDUs to get cpu load ")
                total = 0
                for key, group in groupby(results, lambda x: (
                x.get("metric").get("ns_id"), x.get("metric").get("vnf_member_index"))):
                    ns_id = key[0]
                    vnf_member_index = key[1]
                    cooldown_period, scale_group_descriptor_name = self.process_metric(ns_id, vnf_member_index)
                    list_group = list(group)
                    vdus_num = len(list_group)
                    self.logger.info(
                            f"Found {vdus_num} VDUs of {ns_id} belonging to vnf with index {vnf_member_index}")
                    for result in list_group:
                        vdu = result.get("metric").get("vdu_name")
                        cpu_load = result.get("value")[-1]
                        timestamp = result.get("value")[0]
                        self.logger.info(
                            f"ns-id is {ns_id}. {vdu} has {cpu_load} recorded at "
                            f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}")
                        total += float(cpu_load)
                    self.logger.info(
                        f"Total load for  ns_id:{ns_id} , vnf_member_index:{vnf_member_index},"
                        f" num_of_vdus:{vdus_num} is {total}.Cooldown:{cooldown_period}."
                        f"Scale-group-desc-name:{scale_group_descriptor_name}")

                    self.post_metric(ns_id, vnf_member_index, total, vdus_num, cooldown_period,
                                     scale_group_descriptor_name, timestamp)

            else:
                self.logger.warning(f"No results yet.Retrying in {self.granularity_interval} seconds")
            time.sleep(self.granularity_interval)

    def post_metric(self, ns_id: str, vnf_member_index: str, cpu_load: float, vdu_count: int, cooldown: int,
                    scale_group_name: str, timestamp: float):

        data = {"ns_id": ns_id, "vnf_member_index": vnf_member_index,
                "scaling_group_descriptor": scale_group_name, "cooldown_period": cooldown,
                "vdu_count": vdu_count, "cpu_load": cpu_load,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
                }
        response = requests.post("http://predictors:8000/api/metrics/predict/", json=data,
                                 headers={"Content-Type": "application/json"})
        if response.status_code == 201:
            self.logger.info("Metric posted successfully to predictor")
        else:
            self.logger.critical(f"Could not post to predictor.Status of request:{response.status_code}")


if __name__ == '__main__':
    m = MetricCollector()
    m.get_cpu_load()