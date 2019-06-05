import asyncio
import itertools

import pytest
from asynctest import CoroutineMock, MagicMock

from vnf_detect import VnfDetector

@pytest.mark.asyncio
async def test_vnf_package_ids_token_expired():
    v = VnfDetector()
    mocked_get_auth_token = CoroutineMock()
    mocked_get_auth_token.return_value = "dummy"
    v._token = mocked_get_auth_token.return_value
    v._get_and_set_authentication_token = mocked_get_auth_token

    assert "dummy" == await v._get_and_set_authentication_token(None)
    resp = CoroutineMock()

    first_get_response = MagicMock()
    first_get_response.__aenter__.return_value = resp
    f = asyncio.Future()
    second_get_response = asyncio.Future()
    second_get_response.set_result(f)
    g = asyncio.Future()
    f.json = MagicMock(return_value=g)
    g.set_result([{"_id": 1}, {"_id": 2}])

    context_manager = MagicMock(side_effect=itertools.cycle([first_get_response, second_get_response]))

    mocked_session = MagicMock()
    mocked_session.get = context_manager

    resp.status = 401
    pkg_ids = await v.get_vnf_package_ids(mocked_session)
    assert pkg_ids == [1, 2]
    assert mocked_get_auth_token.await_count == 2


@pytest.mark.asyncio
async def test_vnf_package_ids_token_valid():
    v = VnfDetector()
    mocked_get_auth_token = CoroutineMock()
    mocked_get_auth_token.return_value = "dummy"
    v._token = mocked_get_auth_token.return_value
    v._get_and_set_authentication_token = mocked_get_auth_token

    assert "dummy" == await v._get_and_set_authentication_token(None)
    resp = CoroutineMock()

    first_get_response = MagicMock()
    first_get_response.__aenter__.return_value = resp
    g = asyncio.Future()
    resp.json.return_value = g
    g.set_result([{"_id": 1}, {"_id": 2}])

    context_manager = MagicMock(side_effect=[first_get_response, ])

    mocked_session = MagicMock()
    mocked_session.get = context_manager

    resp.status = 200
    pkg_ids = await v.get_vnf_package_ids(mocked_session)
    assert pkg_ids == [1, 2]
    assert mocked_get_auth_token.await_count == 1


