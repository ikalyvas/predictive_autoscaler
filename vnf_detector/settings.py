OSM_SERVER_IP = "http://34.73.14.235"
LOGIN_URL = OSM_SERVER_IP + '/auth/'
VNF_LIST_URL = OSM_SERVER_IP + '/instances/vnf/list/'
NS_LIST_URL = OSM_SERVER_IP + '/instances/ns/list/'
LOGIN_DATA = {'username': 'admin',
              'password': 'admin',
              'csrfmiddlewaretoken': None,
              'next': ''
              }