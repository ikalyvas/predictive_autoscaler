FROM python:3.6

COPY . /opt/metrics_collector

WORKDIR /opt/metrics_collector

ENV PYTHONPATH /opt:$PYTHONPATH
ENV METRICS_FILE /opt/metric_file_location/metric_cpu.csv
ENV DEFAULT_GRANULARITY 120
ENV HTTP "http://"
ENV HTTPS "https://"
ENV OSM_SERVER_IP "35.228.153.231"
ENV PROMETHEUS_IP $OSM_SERVER_IP
ENV PROMETHEUS_PORT "9091"
ENV NBI_PORT "9999"
ENV NBI_SERVER_PORT $OSM_SERVER_IP:$NBI_PORT
ENV OSM_SOCKET_ADDR $HTTP$OSM_SERVER_IP
ENV NBI_SOCKET_ADDR $HTTPS$NBI_SERVER_PORT
ENV NBI_AUTHENTICATION_URL $NBI_SOCKET_ADDR"/osm/admin/v1/tokens"

RUN pip install -U pip
RUN pip install -r requirements.txt

CMD [ "python", "./metrics_collector.py" ]