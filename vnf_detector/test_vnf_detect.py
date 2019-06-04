import asyncio
import aiohttp

import pytest
from unittest.mock import patch
from asynctest import CoroutineMock


from vnf_detect import VnfDetector

#assert ["a45c27c4-5a6e-459a-97ec-00a002eb5354",
#                    "c9b85064-9fff-41d8-bc4f-a7015af61d0b"] ==
@pytest.mark.asyncio
async def test_vnf_package_ids():
    v = VnfDetector()
    mocked_get_auth_token = CoroutineMock()
    mocked_get_auth_token.return_value = "dummy"
    v._token = mocked_get_auth_token.return_value
    v._get_and_set_authentication_token = mocked_get_auth_token

    assert "dummy" == await v._get_and_set_authentication_token(None)
    #async with aiohttp.ClientSession() as session:
    mocked_session = CoroutineMock()
    resp = CoroutineMock()
    mocked_session.__aenter__ = CoroutineMock()
    mocked_session.__aexit__ = CoroutineMock()
    #resp = CoroutineMock()
    mocked_session.get.return_value = resp
    resp.status = 401
    resp.json.return_value = [{"_id": 1}, {"_id": 2}]
    pkg_ids = await v.get_vnf_package_ids(mocked_session)
    assert pkg_ids == [1, 2]
    assert mocked_get_auth_token.await_count == 1
