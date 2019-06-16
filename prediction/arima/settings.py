DEFAULT_GRANULARITY = 120
TRAINING_PHASE_DELAY = 6 * DEFAULT_GRANULARITY  # time to wait before we start predictions
METRICS_FILE = "metric_cpu.csv"
HTTP = "http://"
HTTPS = "https://"
OSM_SERVER_IP = "35.228.153.231"
NBI_PORT = "9999"
NBI_SERVER_PORT = OSM_SERVER_IP + ":" + NBI_PORT
OSM_SOCKET_ADDR = HTTP + OSM_SERVER_IP
NBI_SOCKET_ADDR = HTTPS + NBI_SERVER_PORT
COOLDOWN = 1
NBI_AUTHENTICATION_URL = NBI_SOCKET_ADDR + "/osm/admin/v1/tokens"
LOGIN_DATA = {"username": "admin",
              "password": "admin"}
