HTTP = "http://"
HTTPS = "https://"
OSM_SERVER_IP = "35.228.24.23"
NBI_PORT = "9999"
NBI_SERVER_PORT = OSM_SERVER_IP + ":" + NBI_PORT
OSM_SOCKET_ADDR = HTTP + OSM_SERVER_IP
NBI_SOCKET_ADDR = HTTPS + NBI_SERVER_PORT
NBI_AUTHENTICATION_URL = NBI_SOCKET_ADDR + "/osm/admin/v1/tokens"
VNF_LIST_URL = HTTPS + OSM_SERVER_IP + '/instances/vnf/list/'
#NS_LIST_URL = OSM_SERVER_IP + '/instances/ns/list/'
LOGIN_DATA = {"username": "admin",
              "password": "admin"}
VNF_PACKAGES_URL = NBI_SOCKET_ADDR + "/osm/vnfpkgm/v1/vnf_packages"
VNFD_URL = NBI_SOCKET_ADDR + "/osm/vnfpkgm/v1/vnf_packages/{vnf_package_id}/vnfd"
VNF_SCHEDULER_CRON_EXPRESSION = '*/1 * * * *'
