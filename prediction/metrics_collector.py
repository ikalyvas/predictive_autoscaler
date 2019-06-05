import yaml
import requests
import time


class MetricCollector(object):

    def __init__(self, config):
        self.prom_ip, self.prom_port = self.read_config(config)
        self.prom_url = "http://" + self.prom_ip + ":" + self.prom_port + "/"


    def read_config(self, config):

        prom_ip = yaml.load(open(config)).get("config").get("PROMETHEUS_IP")
        prom_port = yaml.load(open(config)).get("config").get("PROMETHEUS_PORT")
        return prom_ip, prom_port

    def get_cpu_load(self):
        while True:
            response = requests.get(self.prom_url+"api/v1/query?query=osm_cpu_utilization")
            print(response.status_code)
            resp = response.json()
            results = resp.get("data").get("result")
            if results:
                print(f"Got {len(results)} VDUs to get cpu load ")
                for result in results:
                    vdu = result.get("metric").get("vdu_name")
                    cpu_load = result.get("value")[-1]
                    timestamp = result.get("value")[0]
                    print(f"{vdu} has {cpu_load} recorded at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}")
            time.sleep(10)



if __name__ == '__main__':
    m = MetricCollector('prometheus_cfg.yaml')
    m.get_cpu_load()

