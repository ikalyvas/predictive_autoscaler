import json

import requests
import yaml
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from vnf_detector import settings


class VnfDetector(object):

    def __init__(self):

        self._token = self._get_and_set_authentication_token()
        self._autoscale_vnfds = {}

    def _get_and_set_authentication_token(self):
        """
        :return: token to be used in subsequent requests to NBI API
        """
        headers = {
            'Accept': "application/json",
            'Content-Type': "application/yaml"
        }
        response = requests.post(settings.NBI_AUTHENTICATION_URL,
                                 data=json.dumps(settings.LOGIN_DATA),
                                 headers=headers,
                                 verify=False)

        token = response.json()['id']
        self._token = token
        return token

    def get_vnf_package_ids(self):

        is_token_refreshed = False

        headers = {
            'Accept': "application/json",
            'Authorization': 'Bearer {token}'.format(token=self._token)
         }
        try:
            while not is_token_refreshed:
                response = requests.get(settings.VNF_PACKAGES_URL, headers=headers, verify=False)
                if response.status_code == 401:  # unauthorized we need to refresh the token
                    print "Get new token due to expiration"
                    new_token = self._get_and_set_authentication_token()
                    headers['Authorization'].format(token=new_token)
                    response = requests.get(settings.VNF_PACKAGES_URL, headers=headers, verify=False)
                    is_token_refreshed = True
                else:
                    break

            vnf_packages = response.json()
            print [package["_id"] for package in vnf_packages]
            return [package["_id"] for package in vnf_packages]

        except Exception as e:
            print e
            raise

    def get_vnf_descriptors(self):

        is_token_refreshed = False

        headers = {
            'Accept': "application/yaml,text/plain",
            'Authorization': 'Bearer {token}'.format(token=self._token)
         }

        available_package_ids = self.get_vnf_package_ids()

        for package_id in available_package_ids:

            try:
                while not is_token_refreshed:
                    response = requests.get(settings.VNFD_URL.format(vnf_package_id=package_id),
                                                                     headers=headers,
                                                                     verify=False)
                    if response.status_code == 401: #unauthorized need to refresh the token
                        print "Get a new token due to expiration"
                        new_token = self._get_and_set_authentication_token()
                        headers['Authorization'].format(token=new_token)
                        response = requests.get(settings.VNFD_URL.format(vnf_package_id=package_id),
                                                headers=headers,
                                                verify=False)
                        is_token_refreshed = True
                    else:
                        break
                vnfd =yaml.load(response.content)
                description = vnfd['vnfd:vnfd-catalog']['vnfd'][0]['description']
                if self._is_autoscale(description):
                    self._autoscale_vnfds[package_id] = True
                    print self._autoscale_vnfds
            except Exception as e:
                print e

    def _is_autoscale(self, description):

        if isinstance(description, dict):
            return 'autoscale' in description.keys()
        else:
            raise TypeError("description {description} is not of type dict.Cannot determine if needs autoscale".format(description=str(description)))

    def get_vnfs(self):
        vnf_response = self.session.get(settings.VNF_LIST_URL)
        vnf_instances = vnf_response.json()

        vnfs = vnf_instances.get('instances')

        print 'Found {instances} vnf instances'.format(instances=len(vnfs))
        for vnfd in vnfs:
            print 'vnf_identifier:\t{id}'.format(id=vnfd['id'])
            print json.dumps(vnfd, indent=4, sort_keys=True)


if __name__ == '__main__':

    scheduler = BlockingScheduler()
    v = VnfDetector()
    scheduler.add_job(v.get_vnf_package_ids, CronTrigger.from_crontab(settings.VNF_SCHEDULER_CRON_EXPRESSION))
    scheduler.add_job(v.get_vnf_descriptors, CronTrigger.from_crontab(settings.VNF_SCHEDULER_CRON_EXPRESSION))

    try:
        print 'Starting scheduler'
        scheduler.start()
    except (SystemExit, KeyboardInterrupt):
        raise
