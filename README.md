# Resources #

Tecnhical Guide:
https://osm.etsi.org/images/OSM-Whitepaper-TechContent-ReleaseFOUR-FINAL.pdf


# How to enable gnocchi and ceilometer in Openstack pike #

 After following the instructions in https://serenity-networks.com/how-to-install-openstack-ocata-on-a-single-server-using-devstack/
 Insert into local.conf the following lines
 ```
    # gnocchi
    enable_plugin gnocchi https://github.com/gnocchixyz/gnocchi.git stable/4.2
    enable_service gnocchi-api,gnocchi-metricd
    # ceilometer
    enable_plugin ceilometer https://git.openstack.org/openstack/ceilometer.git stable/pike
    CEILOMETER_BACKEND=gnocchi
   ```
   After installation finishes gnocchi and ceilometer should be up and running.
   Check it with the following steps
   
   ```
   login to openstack dashboard and download admin-openrc.sh (v3)
   copy to openstack vm
   source admin-openrc.sh
   export OS_AUTH_TYPE=password
   gnocchi status
   gnocchi measures show --resource-id <vnf instance id from OSM MANO> cpu_util

   ```
  
# How to collect metrics in OSM MON module

  Go to OSM VM and follow the steps:
  
  ```
  export OSM_HOSTNAME=10.166.0.11 or the local ip of the OSM VM
  ```
  Adjust the granularity to match this of gnocchi in Openstack
  
  ```
  docker service update --force --env-add OSM_DEFAULT_GRANULARITY=300 osm_mon
  docker service update --force --env-add OSMMON_LOG_LEVER=DEBUG osm_mon
  ```
  then start exporting metrics with
  ```
  osm ns-metric-export --ns ns_metrics_ubuntu --vnf 1 --vdu ubuntu_vnf-VM --metric average_memory
_utilization
  ```
  
  On the other hand, exporting metrics in R5 is not needed.
  In R5 it seems that every 30 seconds a query to prometheus container is executed and every available metric in VNFD level(related to scaling) is retrieved.
  ```
  04/01/2019 02:13:14 PM - osm_mon.evaluator.evaluator - INFO - Querying Prometheus: http://prometheus:9090/api/v1/query?query=osm_cpu_utilization{ns_id="4438699a-cd74-458d-bf81-a8509ffac94a",vdu_name="ns_with_metrics_autoscale-1-ubuntu_vnf-VM-1",vnf_member_index="1"}
04/01/2019 02:13:14 PM - osm_mon.evaluator.evaluator - INFO - Metric value: 0.3732249252
04/01/2019 02:13:14 PM - osm_mon.evaluator.evaluator - INFO - Querying Prometheus: http://prometheus:9090/api/v1/query?query=osm_cpu_utilization{ns_id="4438699a-cd74-458d-bf81-a8509ffac94a",vdu_name="ns_with_metrics_autoscale-1-ubuntu_vnf-VM-1",vnf_member_index="1"}
04/01/2019 02:13:14 PM - osm_mon.evaluator.evaluator - INFO - Querying Prometheus: http://prometheus:9090/api/v1/query?query=osm_cpu_utilization{ns_id="4438699a-cd74-458d-bf81-a8509ffac94a",vdu_name="ns_with_metrics_autoscale-2-ubuntu_vnf-VM-1",vnf_member_index="2"}
04/01/2019 02:13:14 PM - osm_mon.evaluator.evaluator - INFO - Metric value: 0.3732249252
04/01/2019 02:13:14 PM - osm_mon.evaluator.evaluator - INFO - Querying Prometheus: http://prometheus:9090/api/v1/query?query=osm_cpu_utilization{ns_id="4438699a-cd74-458d-bf81-a8509ffac94a",vdu_name="ns_with_metrics_autoscale-2-ubuntu_vnf-VM-1",vnf_member_index="2"}
04/01/2019 02:13:14 PM - osm_mon.evaluator.evaluator - INFO - Metric value: 0.3732249252
04/01/2019 02:13:14 PM - osm_mon.evaluator.evaluator - INFO - Metric value: 0.3732249252
```
This will send message to kafka bus for collecting metric memory_utilization about the
vnf index:1 and for vdu ubuntu_vnf-VM .
On the other side MON container will receive the message and start collecting from gnocchi at openstack.
When it has collected the metrics for this vm,it will post back to a metrics_response kafka topic.
We can see the metrics with
  ```
   docker logs -f <mon_container_id>
  ```
  
  If you want to install OSM along with the PM stack, run the installer as follows:
```
./install_osm.sh --pm_stack
```
If you just want to add the PM stack to an existing OSM R4 Lightweight build, run the installer as follows:
```
 ./install_osm.sh -o pm_stack
 ```
This will install three additional docker containers (Kafka Exporter, Prometheus and Grafana)

If you need to remove it at some point in time, just run the following command:
```
docker stack rm osm_metrics
```
If you need to deploy the stack again after being removed:
```
docker stack deploy -c /etc/osm/docker/osm_metrics/docker-compose.yml osm_metrics
```

Testing the OSM PM Stack
1. Create a continuous metric, that runs in the background as indicated in the first section.

2. Check if the Kafka Exporter is serving the metric to Prometheus, by visiting http://1.2.3.4:12340/metrics, replacing 1.2.3.4 with the IP address of your host. Metrics should appear in the following text format:
```
# HELP kafka_exporter_topic_average_memory_utilization 
# TYPE kafka_exporter_topic_average_memory_utilization gauge
kafka_exporter_topic_average_memory_utilization{resource_uuid="5599ce48-a830-4c51-995e-a663e590952f",} 200.0
# HELP kafka_exporter_topic_cpu_utilization 
# TYPE kafka_exporter_topic_cpu_utilization gauge
kafka_exporter_topic_cpu_utilization{resource_uuid="5599ce48-a830-4c51-995e-a663e590952f",} 0.7950777152296741
```
Note: if metrics appear at MON logs but not at this web service, we may have hit a rare issue (under investigation), where Kafka Exporter loses connection to the bus.

To confirm this issue, access the kafka-exporter container and check the log for a message like 'dead coordinator' (tail kafka-topic-exporter.log)
To recover, just reload the service using 

```
docker service update --force osm_metrics_kafka-exporter

```
3. Visit Grafana at http://1.2.3.4:3000, replacing 1.2.3.4 with the IP address of your host. Login with admin/admin credentials and visit the OSM Sample Dashboard. It should already show graphs for CPU and Memory. You can clone them and customize as desired.
4. Prometheus can also be used to see the graph by issuing ```kafka_exporter_topic_cpu_utilization```(OSM R4) or ```osm_cpu_utilization```(OSM R5)  in the metric field. 
5. Collect metrics through Prometheus API with 

For OSM R4 you can use :
```
curl 'http://127.0.0.1:9091/api/v1/query_range?query=kafka_exporter_topic_cpu_utili
zation&start=2019-03-21T20:20:00.000Z&end=2019-03-21T23:20:00.000Z&step=15s'
```
or for OSM R5
```
curl 'http://127.0.0.1:9091/api/v1/query_range?query=osm_cpu_utili
zation&start=2019-03-21T20:20:00.000Z&end=2019-03-21T23:20:00.000Z&step=15s'
```
The result is of the following form:
```
{"status":"success",
"data":{"resultType":"matrix","result":
[{"metric":{"__name__":"osm_cpu_utilization",
           "instance":"mon:8000",
           "job":"prometheus",
           "ns_id":"4438699a-cd74-458d-bf81-a8509ffac94a",
           "vdu_name":"ns_with_metrics_autoscale-1-ubuntu_vnf-VM-1",
           "vnf_member_index":"1"},
           "values":[[1554126885,"3.3436022593"],
           [1554126900,"3.3436022593"],
           [1554126915,"3.3436022593"],
           [1554126930,"3.3436022593"],
           [1554126945,"3.3436022593"],
           [1554126960,"3.3436022593"],
           [1554126975,"3.3436022593"],
           [1554126990,"3.3436022593"],
           [1554127005,"3.3436022593"],
           [1554127020,"3.3436022593"],
           [1554127035,"3.3436022593"],
           [1554127050,"3.3436022593"],
           [1554127065,"3.3436022593"],
           [1554127095,"3.3436022593"],
           [1554127110,"3.3436022593"],
           [1554127125,"3.3436022593"],
           [1554127140,"3.3436022593"]]},
    {"metric":{"__name__":"osm_cpu_utilization",
    "instance":"mon:8000",
    "job":"prometheus",
    "ns_id":"4438699a-cd74-458d-bf81-a8509ffac94a",
    "vdu_name":"ns_with_metrics_autoscale-2-ubuntu_vnf-VM-1",
    "vnf_member_index":"2"},
    "values":[[1554126915,"3.4969479262"],[1554126930,"3.4969479262"],
    [1554126945,"3.4969479262"],
    [1554126960,"3.4969479262"],
    [1554126975,"3.4969479262"],
    [1554126990,"3.4969479262"],
    [1554127005,"3.4969479262"],
    [1554127020,"3.4969479262"],
    [1554127035,"3.4969479262"],
    [1554127050,"3.4969479262"],
    [1554127065,"3.4969479262"],
    [1554127080,"3.4969479262"],
    [1554127095,"3.4969479262"],
    [1554127110,"3.4969479262"],
    [1554127125,"3.4969479262"],
    [1554127140,"3.4969479262"]]}]}}```

# How to scale out / scale in a vdu in an NS from OSM #

1. Use a VNFD following the example found in https://osm.etsi.org/wikipub/index.php/OSM_Autoscaling
2. After having created an NS and the constituent vnfs go to postman
  * Get a valid token
  * Issue https://35.228.24.156:9999/osm/nslcm/v1/ns_instances/<ns-id>/scale
    where ns-id is the id taken from OSM
    The body of the request is of the following form
```
```{"scaleType":"SCALE_VNF",
"scaleVnfData": {"scaleVnfType":"SCALE_OUT",
"scaleByStepData": {"scaling-group-descriptor": "vnf_autoscale","member-vnf-index": "1"}}}
```

```__vnf_autoscale__``` is a descriptor defined at VNFD level.(it is a custome name in other words to define a scaling descriptor)

