from typing import Any, TypeVar, Unpack, overload

import aiohttp
import requests
from pydantic import ValidationError

from .models import (
    D3_PLUGIN_ENDPOINT,
    D3_PLUGIN_MODULE_REG_ENDPOINT,
    PluginError,
    PluginException,
    PluginResponse,
    TypedBlob,
)

RetType = TypeVar("RetType")


###############################################################################
# Low level request
def d3_api_request(
    method: str,
    hostname: str,
    port: int,
    url_endpoint: str,
    **kwargs,
) -> Any:
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
) -> Any:
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
    timeout_ms: float | None = None,
) -> Any:
    return await d3_api_arequest(
        "GET",
        hostname,
        port,
        url_endpoint,
        json=json,
        timeout=aiohttp.ClientTimeout(timeout_ms) if timeout_ms else None,
    )


async def d3_api_apost(
    hostname: str,
    port: int,
    url_endpoint: str,
    json: dict | None = None,
    timeout_ms: float | None = None,
) -> Any:
    return await d3_api_arequest(
        "POST",
        hostname,
        port,
        url_endpoint,
        json=json,
        timeout=aiohttp.ClientTimeout(timeout_ms) if timeout_ms else None,
    )


async def d3_api_aput(
    hostname: str,
    port: int,
    url_endpoint: str,
    json: dict | None = None,
    timeout_ms: float | None = None,
) -> Any:
    return await d3_api_arequest(
        "PUT",
        hostname,
        port,
        url_endpoint,
        json=json,
        timeout=aiohttp.ClientTimeout(timeout_ms) if timeout_ms else None,
    )


@overload
async def d3_api_aplugin(
    hostname: str, port: int, plugin_blob: dict, timeout_ms: float | None = None
) -> PluginResponse: ...


@overload
async def d3_api_aplugin(
    hostname: str, port: int, plugin_blob: TypedBlob[RetType], timeout_ms: float | None = None
) -> PluginResponse[RetType]: ...


async def d3_api_aplugin(
    hostname: str,
    port: int,
    plugin_blob: dict | TypedBlob[RetType],
    timeout_ms: float | None = None,
) -> PluginResponse | PluginResponse[RetType]:
    # Extract blob from TypedBlob if necessary
    if isinstance(plugin_blob, TypedBlob):
        json_data = plugin_blob.blob
        is_typed = True
    else:
        json_data = plugin_blob
        is_typed = False

    response: Any = await d3_api_arequest(
        "POST",
        hostname,
        port,
        D3_PLUGIN_ENDPOINT,
        json=json_data,
        timeout=aiohttp.ClientTimeout(timeout_ms) if timeout_ms else None,
    )

    try:
        if is_typed:
            return PluginResponse[RetType].model_validate(response)
        else:
            return PluginResponse.model_validate(response)
    except ValidationError:
        error_response: PluginError = PluginError.model_validate(response)
        raise PluginException(
            status=error_response.status,
            d3Log=error_response.d3Log,
            pythonLog=error_response.pythonLog,
        ) from None


async def d3_api_aregister_module(
    hostname: str, port: int, json: dict | None = None, timeout_ms: float | None = None
) -> Any:
    try:
        return await d3_api_arequest(
            "POST",
            hostname,
            port,
            D3_PLUGIN_MODULE_REG_ENDPOINT,
            json=json,
            timeout=aiohttp.ClientTimeout(timeout_ms) if timeout_ms else None,
        )
    except Exception as e:
        raise Exception(
            f"Failed to register module '{json.get('moduleName') if json else ''}': {e}"
        ) from e


###############################################################################
# API sync interface
def d3_api_get(
    hostname: str,
    port: int,
    url_endpoint: str,
    json: dict | None = None,
    timeout_ms: float | None = None,
) -> Any:
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
    timeout_ms: float | None = None,
) -> Any:
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
    timeout_ms: float | None = None,
) -> Any:
    return d3_api_request(
        "PUT",
        hostname,
        port,
        url_endpoint,
        json=json,
        timeout=timeout_ms / 1000 if timeout_ms else None,
    )


@overload
def d3_api_plugin(
    hostname: str, port: int, plugin_blob: dict, timeout_ms: float | None = None
) -> PluginResponse: ...


@overload
def d3_api_plugin(
    hostname: str, port: int, plugin_blob: TypedBlob[RetType], timeout_ms: float | None = None
) -> PluginResponse[RetType]: ...


def d3_api_plugin(
    hostname: str,
    port: int,
    plugin_blob: dict | TypedBlob[RetType],
    timeout_ms: float | None = None,
) -> PluginResponse | PluginResponse[RetType]:
    # Extract blob from TypedBlob if necessary
    if isinstance(plugin_blob, TypedBlob):
        json_data = plugin_blob.blob
        is_typed = True
    else:
        json_data = plugin_blob
        is_typed = False

    response = d3_api_request(
        "POST",
        hostname,
        port,
        D3_PLUGIN_ENDPOINT,
        json=json_data,
        timeout=timeout_ms / 1000 if timeout_ms else None,
    )

    try:
        if is_typed:
            return PluginResponse[RetType].model_validate(response)
        else:
            return PluginResponse.model_validate(response)
    except ValidationError:
        error_response: PluginError = PluginError.model_validate(response)
        raise PluginException(
            status=error_response.status,
            d3Log=error_response.d3Log,
            pythonLog=error_response.pythonLog,
        ) from None


def d3_api_register_module(
    hostname: str,
    port: int,
    json: dict | None = None,
    timeout_ms: float | None = None,
) -> Any:
    try:
        return d3_api_request(
            "POST",
            hostname,
            port,
            D3_PLUGIN_MODULE_REG_ENDPOINT,
            json=json,
            timeout=timeout_ms / 1000 if timeout_ms else None,
        )
    except Exception as e:
        raise RuntimeError(
            f"Failed to register module '{json.get('moduleName') if json else ''}': {e}"
        ) from e
