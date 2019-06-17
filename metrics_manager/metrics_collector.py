import logging
import time
import csv
from itertools import groupby
import os

import yaml
import requests


class MetricCollector(object):

    def __init__(self, config):
        self.prom_ip = self.read_config(config, "PROMETHEUS_IP")
        self.prom_port = self.read_config(config, "PROMETHEUS_PORT")
        self.granularity_interval = self.read_config(config, "DEFAULT_GRANULARITY")
        self.metric_file = os.environ.get("METRICS_FILE")
        self.prom_url = "http://" + self.prom_ip + ":" + self.prom_port + "/"
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s]  %(message)s",
            handlers=[
                logging.FileHandler("{0}.log".format("metrics_collector")),
                logging.StreamHandler()
            ])

        self.logger = logging.getLogger('prediction.metrics_collector')

    def read_config(self, config, field):

        return yaml.load(open(config)).get("prometheus_config").get(field)


    def get_cpu_load(self):

        with open(self.metric_file, newline='', mode='w') as f:
            fieldnames = ["ID", "NS_ID", "VNF_MEMBER_INDEX", "TIMESTAMP", "CPU_LOAD", "VDU_COUNT"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader() if f.tell() == 0 else True
            id_ = 0
            while True:
                response = requests.get(self.prom_url + "api/v1/query?query=osm_cpu_utilization")
                resp = response.json()
                results = resp.get("data").get("result")
                if results:
                    print(f"Got {len(results)} VDUs to get cpu load ")
                    total = 0
                    for key, group in groupby(results, lambda x: (
                    x.get("metric").get("ns_id"), x.get("metric").get("vnf_member_index"))):
                        ns_id = key[0]
                        vnf_member_index = key[1]
                        list_group = list(group)
                        vdus_num = len(list_group)
                        self.logger.info(
                            f"Found {vdus_num} VDUs of {ns_id} belonging to vnf with index {vnf_member_index}")
                        for result in list_group:
                            vdu = result.get("metric").get("vdu_name")
                            cpu_load = result.get("value")[-1]
                            timestamp = result.get("value")[0]
                            self.logger.info(
                                f"ns-id is {ns_id}. {vdu} has {cpu_load} recorded at {time.strftime('%Y-%m-%d %H:%M:%S',
                                                                                                    time.localtime(
                                                                                                        timestamp))}")
                            total += float(cpu_load)
                        self.logger.info(
                            f"Total load for  ns_id:{ns_id} , vnf_member_index:{vnf_member_index}, num_of_vdus:{vdus_num} is {total}")
                        writer.writerow({"ID": id_, "NS_ID": ns_id, "VNF_MEMBER_INDEX": vnf_member_index,
                                         "TIMESTAMP": timestamp, "CPU_LOAD": total, "VDU_COUNT": vdus_num})
                        f.flush()
                        id_ += 1
                else:
                    self.logger.warning(f"No results yet.Retrying in {self.granularity_interval} seconds")

                time.sleep(self.granularity_interval)


if __name__ == '__main__':
    m = MetricCollector('prometheus_cfg.yaml')
    m.get_cpu_load()
