import aiohttp
import requests
from typing import Unpack, TypeVar
from .core import PluginResponse, TypedBlob, D3_PLUGIN_ENDPOINT


RetType = TypeVar("RetType")


###############################################################################
# Low level request
def d3_api_request(
    method: str,
    hostname: str,
    port: int,
    url_endpoint: str,
    **kwargs,
) -> dict:
    url: str = f"http://{hostname}:{port}/{url_endpoint.lstrip('/')}"
    response = requests.request(
        method,
        url,
        **kwargs,
    )
    return response.json()


async def d3_api_arequest(
    method: str,
    hostname: str,
    port: int,
    url_endpoint: str,
    **kwargs: Unpack[aiohttp.client._RequestOptions],
) -> dict:
    url: str = f"http://{hostname}:{port}/{url_endpoint.lstrip('/')}"
    async with aiohttp.ClientSession() as session:
        async with session.request(
            method,
            url,
            **kwargs,
        ) as response:
            return await response.json()


###############################################################################
# API async interface
async def d3_api_aget(
    hostname: str,
    port: int,
    url_endpoint: str,
    json: dict | None = None,
    timeout_ms: float|None = None
) -> dict:
    return await d3_api_arequest(
        "GET",
        hostname,
        port,
        url_endpoint,
        json=json,
        timeout=aiohttp.ClientTimeout(timeout_ms) if timeout_ms else None
    )

async def d3_api_apost(
    hostname: str,
    port: int,
    url_endpoint: str,
    json: dict | None = None,
    timeout_ms: float|None = None
) -> dict:
    return await d3_api_arequest(
        "POST",
        hostname,
        port,
        url_endpoint,
        json=json,
        timeout=aiohttp.ClientTimeout(timeout_ms) if timeout_ms else None
    )

async def d3_api_aput(
    hostname: str,
    port: int,
    url_endpoint: str,
    json: dict | None = None,
    timeout_ms: float|None = None
) -> dict:
    return await d3_api_arequest(
        "PUT",
        hostname,
        port,
        url_endpoint,
        json=json,
        timeout=aiohttp.ClientTimeout(timeout_ms) if timeout_ms else None
    )

async def d3_api_aplugin(
    hostname: str,
    port: int,
    plugin_blob: dict,
    timeout_ms: float|None = None
) -> PluginResponse:
    return PluginResponse.model_validate(
        await d3_api_arequest(
            "POST",
            hostname,
            port,
            D3_PLUGIN_ENDPOINT,
            json=plugin_blob,
            timeout=aiohttp.ClientTimeout(timeout_ms) if timeout_ms else None
        )
    )

async def d3_api_typed_aplugin(
    hostname: str,
    port: int,
    plugin_blob:
    TypedBlob[RetType],
    timeout_ms: float|None = None
) -> PluginResponse[RetType]:
    return PluginResponse[plugin_blob.return_type].model_validate(
        await d3_api_arequest(
            "POST",
            hostname,
            port,
            D3_PLUGIN_ENDPOINT,
            json=plugin_blob.blob,
            timeout=aiohttp.ClientTimeout(timeout_ms) if timeout_ms else None
        )
    )


###############################################################################
# API sync interface
def d3_api_get(
    hostname: str,
    port: int,
    url_endpoint: str,
    json: dict | None = None,
    timeout_ms: float|None = None,
) -> dict:
    return d3_api_request(
        "GET",
        hostname,
        port,
        url_endpoint,
        json=json,
        timeout=timeout_ms / 1000 if timeout_ms else None,
    )

def d3_api_post(
    hostname: str,
    port: int,
    url_endpoint: str,
    json: dict | None = None,
    timeout_ms: float|None = None,
) -> dict:
    return d3_api_request(
        "POST",
        hostname,
        port,
        url_endpoint,
        json=json,
        timeout=timeout_ms / 1000 if timeout_ms else None,
    )

def d3_api_put(
    hostname: str,
    port: int,
    url_endpoint: str,
    json: dict | None = None,
    timeout_ms: float|None = None,
) -> dict:
    return d3_api_request(
        "PUT",
        hostname,
        port,
        url_endpoint,
        json=json,
        timeout=timeout_ms / 1000 if timeout_ms else None,
    )

def d3_api_plugin(
    hostname: str, port: int, plugin_blob: dict, timeout_ms: float|None = None
) -> PluginResponse:
    return PluginResponse.model_validate(
        d3_api_request(
            "POST",
            hostname,
            port,
            D3_PLUGIN_ENDPOINT,
            json=plugin_blob,
            timeout=timeout_ms / 1000 if timeout_ms else None,
        )
    )

def d3_api_typed_plugin(
    hostname: str, port: int, plugin_blob: TypedBlob[RetType], timeout_ms: float|None = None
    ) -> PluginResponse[RetType]:
    return PluginResponse[plugin_blob.return_type].model_validate(
        d3_api_request(
            "POST",
            hostname,
            port,
            D3_PLUGIN_ENDPOINT,
            json=plugin_blob.blob,
            timeout=timeout_ms / 1000 if timeout_ms else None,
        )
    )
