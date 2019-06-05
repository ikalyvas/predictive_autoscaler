import json
import asyncio
import aiohttp

import requests
import yaml
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from vnf_detector import settings


class VnfDetector(object):

    def __init__(self, loop=None):
        logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)
        self.log = logging.getLogger('vnf_detector')
        self._autoscale_vnfds = {}
        self.loop = loop

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
            self.log.info(f"Got token due to expiration {self._token}")

        else:
            async with aiohttp.ClientSession() as session:
                async with session.post(settings.NBI_AUTHENTICATION_URL,
                                        json=settings.LOGIN_DATA,
                                        headers=headers,
                                        ssl=False) as response:
                    json_resp = await response.json()
                    self._token = json_resp["id"]
                    self.log.info(f"Got token {self._token}")

        return self._token

    async def get_vnf_package_ids(self, session):

        headers = {
            'Accept': "application/json",
            'Authorization': 'Bearer {token}'.format(token=self._token)
         }

        try:

            async with session.get(settings.VNF_PACKAGES_URL, headers=headers, ssl=False) as response:

                status_code = response.status
                if status_code == 401:
                    new_token = await self._get_and_set_authentication_token(session)
                    headers['Authorization'] = 'Bearer ' + new_token
                    response = await session.get(settings.VNF_PACKAGES_URL, headers=headers, ssl=False)

                vnf_packages = await response.json()
                self.log.warning(f"vnf packages is {type(vnf_packages)}")
                self.log.warning(vnf_packages)
                return [package["_id"] for package in vnf_packages]

        except Exception as e:
            self.log.exception(e)
            raise

    async def get_vnf_descriptors(self, session):


        available_package_ids = await self.get_vnf_package_ids(session)

        headers = {
            'Accept': "application/yaml,text/plain",
            'Authorization': 'Bearer {token}'.format(token=self._token)
        }

        for package_id in available_package_ids:

            try:

                async with session.get(settings.VNFD_URL.format(vnf_package_id=package_id),
                                                                     headers=headers,
                                                                     ssl=False) as response:
                    status_code = response.status
                    if status_code == 401: #unauthorized need to refresh the token
                        new_token = await self._get_and_set_authentication_token(session)
                        headers['Authorization'] = 'Bearer ' + new_token
                        response = await session.get(settings.VNFD_URL.format(vnf_package_id=package_id),
                                                headers=headers,
                                                ssl=False)

                    vnfd = yaml.load(await response.text())
                    self._is_autoscale(vnfd, package_id)

            except Exception as e:
                self.log.exception(e)

    def _is_autoscale(self, vnfd, package_id):

        if 'scaling-group-descriptor' in vnfd['vnfd:vnfd-catalog']['vnfd'][0]:
            self.log.info(f"{package_id} has autoscale support")
            self._autoscale_vnfds[package_id] = True

    def get_vnfs(self):
        vnf_response = self.session.get(settings.VNF_LIST_URL)
        vnf_instances = vnf_response.json()

        vnfs = vnf_instances.get('instances')

        print(f'Found {len(vnfs)} vnf instances')
        for vnfd in vnfs:
            print('vnf_identifier:\t{id}'.format(id=vnfd['id']))
            print(json.dumps(vnfd, indent=4, sort_keys=True))

    async def main(self):

        await self._get_and_set_authentication_token(None)

        while True:
            async with aiohttp.ClientSession() as session:
                await asyncio.gather(self.get_vnf_descriptors(session), return_exceptions=False)
            await asyncio.sleep(900)

    def start(self):

        loop = self.loop or asyncio.get_event_loop()
        loop.run_until_complete(self.main())


if __name__ == '__main__':

    v = VnfDetector()

    try:
        print('Starting async loop')
        v.start()
    except (SystemExit, KeyboardInterrupt):
        raise
