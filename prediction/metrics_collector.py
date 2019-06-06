import math

import yaml
import requests
import time
import csv


class MetricCollector(object):

    def __init__(self, config):
        self.prom_ip, self.prom_port = self.read_config(config)
        self.prom_url = "http://" + self.prom_ip + ":" + self.prom_port + "/"


    def read_config(self, config):

        prom_ip = yaml.load(open(config)).get("config").get("PROMETHEUS_IP")
        prom_port = yaml.load(open(config)).get("config").get("PROMETHEUS_PORT")
        return prom_ip, prom_port

    def get_cpu_load(self):
        with open('metric_cpu.csv', newline='', mode='a') as f:
            fieldnames = ["ID", "TIMESTAMP", "CPU_LOAD"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            id_ = 0
            while True:
                response = requests.get(self.prom_url+"api/v1/query?query=osm_cpu_utilization")
                resp = response.json()
                results = resp.get("data").get("result")
                if results:
                    print(f"Got {len(results)} VDUs to get cpu load ")
                    total = 0
                    for result in results:
                        vdu = result.get("metric").get("vdu_name")
                        cpu_load = result.get("value")[-1]
                        timestamp = result.get("value")[0]
                        print(f"{vdu} has {cpu_load} recorded at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}")
                        total += float(cpu_load)
                    avg = total / len(results)
                    writer.writerow({"ID": id_, "TIMESTAMP": timestamp, "CPU_LOAD": avg})
                    f.flush()
                    id_ += 1


                time.sleep(1)

if __name__ == '__main__':
    m = MetricCollector('prometheus_cfg.yaml')
    m.get_cpu_load()

