import json

import requests
import yaml
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from vnf_detector import settings


class VnfDetector(object):

    def __init__(self):

        self._token = self._get_authentication_token()
        self._autoscale_vnfds = {}

    def _get_authentication_token(self):
        """

        :return: token to be used in subsequent requests to NBI API
        """
        headers = {
            'Accept': "application/json",
            'Content-Type': "application/json"
        }
        response = requests.post(settings.NBI_AUTHENTICATION_URL, data=settings.LOGIN_DATA, headers=headers, verify=False)

        token = response.json()['id']

        return token

    def get_vnf_package_ids(self):

        headers = {
            'Accept': "application/json",
            'Authorization': 'Bearer ' + self._token
         }
        try:
            response = requests.get(settings.VNF_PACKAGES_URL, headers=headers, verify=False)

        except requests.exceptions.RequestException:
            print "Re-issue token authenticate due to expiration"
            self._get_authentication_token()

        vnf_packages = response.json()[0]
        return [package["_id"] for package in vnf_packages]

    def get_vnf_descriptors(self):

        headers = {
            'Accept': "application/yaml,text/plain",
            'Authorization': 'Bearer ' + self._token
         }

        available_package_ids = self.get_vnf_package_ids()

        for package_id in available_package_ids:

            try:
                response = requests.get(settings.VNFD_URL.format(vnf_package_id=package_id), headers=headers, verify=False)
                vnfd =yaml.load(response.content)
                description = vnfd['vnfd:vnfd-catalog']['vnfd'][0]['description']
            except requests.exceptions.RequestException:
                print "Re-issue token authenticate due to expiration"
                self._get_authentication_token()
            else:
                if self._is_autoscale(description):
                    self._autoscale_vnfds[package_id] = True



        vnf_packages = response.json()[0]
        return [package["_id"] for package in vnf_packages]

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


    def post_to_metrics_manager(self):
        pass


if __name__ == '__main__':

    scheduler = BlockingScheduler()
    v = VnfDetector()
    scheduler.add_job(v.get_vnfs, CronTrigger.from_crontab(settings.VNF_SCHEDULER_CRON_EXPRESSION))

    try:
        print 'Starting scheduler'
        scheduler.start()
    except (SystemExit, KeyboardInterrupt):
        raise
