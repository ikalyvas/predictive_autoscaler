import json
import asyncio
import aiohttp

import requests
import yaml
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from vnf_detector import settings


class VnfDetector(object):

    def __init__(self, loop=None):

        self._token = self.get_token(loop)
        self._autoscale_vnfds = {}
        self.loop = loop

    def get_token(self, loop):

         loop = loop or asyncio.new_event_loop()
         get_token_task = asyncio.create_task(self._get_and_set_authentication_token(None))

         while not get_token_task.done():

            try:
                 get_token_task.result()
            except asyncio.InvalidStateError as e:
                print(f"Getting token is still ongoing")
            except Exception as e:
                print(f"Getting token raised exception. {e}")


    async def _get_and_set_authentication_token(self, session):
        """
        :return: token to be used in subsequent requests to NBI API
        """
        headers = {
            'Accept': "application/json",
            'Content-Type': "application/yaml"
        }
        if session:
            response = await session.post(settings.NBI_AUTHENTICATION_URL,
                                 json=settings.LOGIN_DATA,
                                 headers=headers,
                                 ssl=False)
            json_resp = await response.json()
            self._token = json_resp["id"]
            print(f"Got token due to expiration {self._token}")

        else:
            async with aiohttp.ClientSession() as session:
                async with session.post(settings.NBI_AUTHENTICATION_URL,
                                        json=settings.LOGIN_DATA,
                                        headers=headers,
                                        ssl=False) as response:
                    json_resp = await response.json()
                    self._token = json_resp["id"]
                    print(f"Got token {self._token}")

        return self._token

    async def get_vnf_package_ids(self, session):

        is_token_refreshed = False

        headers = {
            'Accept': "application/json",
            'Authorization': 'Bearer {token}'.format(token=self._token)
         }
        try:
            while not is_token_refreshed:
                async with session.get(settings.VNF_PACKAGES_URL, headers=headers, ssl=False) as response:

                    status_code = response.status
                    print(f"Got {status_code}")
                    if status_code == 401:
                        new_token = await self._get_and_set_authentication_token(session)
                        headers['Authorization'].format(token=new_token)
                        response = await session.get(settings.VNF_PACKAGES_URL, headers=headers, ssl=False)
                        is_token_refreshed = True
                    else:
                        #break
                        pass

                    vnf_packages = await response.json()
                    print([package["_id"] for package in vnf_packages])
                    return [package["_id"] for package in vnf_packages]

        except Exception as e:
            print(e)
            raise

    def get_vnf_descriptors(self):

        is_token_refreshed = False

        headers = {
            'Accept': "application/yaml,text/plain",
            'Authorization': 'Bearer {token}'.format(token=self._token)
         }

        available_package_ids =  self.get_vnf_package_ids()

        for package_id in available_package_ids:

            try:
                while not is_token_refreshed:
                    response = requests.get(settings.VNFD_URL.format(vnf_package_id=package_id),
                                                                     headers=headers,
                                                                     verify=False)
                    if response.status_code == 401: #unauthorized need to refresh the token
                        print("Get a new token due to expiration")
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
                    print(self._autoscale_vnfds)
            except Exception as e:
                print(e)

    def _is_autoscale(self, description):

        if isinstance(description, dict):
            return 'autoscale' in description.keys()
        else:
            raise TypeError("description {description} is not of type dict.Cannot determine if needs autoscale".format(description=str(description)))

    def get_vnfs(self):
        vnf_response = self.session.get(settings.VNF_LIST_URL)
        vnf_instances = vnf_response.json()

        vnfs = vnf_instances.get('instances')

        print(f'Found {len(vnfs)} vnf instances')
        for vnfd in vnfs:
            print('vnf_identifier:\t{id}'.format(id=vnfd['id']))
            print(json.dumps(vnfd, indent=4, sort_keys=True))

    async def main(self):

        #self._token = await self._get_and_set_authentication_token()

        async with aiohttp.ClientSession() as session:
            #coros = [self.get_vnf_descriptors(session, url) for url in ]

            #vnf_descriptors = await asyncio.gather(self.get_vnf_descriptors(session, 'http://python.org')
            vnf_pkg_ids = await asyncio.gather(self.get_vnf_package_ids(session))
            print(f"Returned {vnf_pkg_ids}")

    def start(self):

        loop = self.loop or asyncio.new_event_loop()
        #loop.run_until_complete(self._get_and_set_authentication_token(None))
        loop.run_until_complete(self.main())


if __name__ == '__main__':

    scheduler = BlockingScheduler()
    v = VnfDetector()
    scheduler.add_job(v.start, CronTrigger.from_crontab(settings.VNF_SCHEDULER_CRON_EXPRESSION))
    #scheduler.add_job(v.get_vnf_descriptors, CronTrigger.from_crontab(settings.VNF_SCHEDULER_CRON_EXPRESSION))

    try:
        print('Starting async loop')
        scheduler.start()
    except (SystemExit, KeyboardInterrupt):
        raise
