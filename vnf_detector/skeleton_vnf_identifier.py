import requests
from vnf_detector import settings


class VnfDetector(object):

    def __init__(self):

        session = requests.Session()
        session.get(settings.LOGIN_URL)

        # prepare headers for json response and update csrf token

        session.headers.update({'Accept': 'application/json'})

        settings.LOGIN_DATA.update({'csrfmiddlewaretoken': session.cookies.get('csrftoken')})

        # do the post with login data and csrf token

        r = session.post(settings.LOGIN_URL, data= settings.LOGIN_DATA)

        self.session = session

    def get_vnfs(self):
        vnf_response = self.session.get(settings.VNF_LIST_URL)
        vnf_instances = vnf_response.json()

        vnfs = vnf_instances.get('instances')

        print 'Found {instances} vnf instances'.format(instances=len(vnfs))
        for vnfd in vnfs:
            print 'vnf_identifier:\t{id}'.format(id=vnfd['id'])


v = VnfDetector()
v.get_vnfs()
