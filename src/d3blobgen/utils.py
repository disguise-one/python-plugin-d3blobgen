from enum import StrEnum
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
# Plugin endpoint constants
def get_plugin_endpoint_url(hostname: str, port: int) -> str:
    """Get the full URL for the plugin execution endpoint."""
    return f"http://{hostname}:{port}/{D3_PLUGIN_ENDPOINT}"


def get_plugin_module_register_url(hostname: str, port: int) -> str:
    """Get the full URL for the module registration endpoint."""
    return f"http://{hostname}:{port}/{D3_PLUGIN_MODULE_REG_ENDPOINT}"


###############################################################################
# Low level request
class Method(StrEnum):
    GET = "GET"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


def d3_api_request(
    method: Method,
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
    method: Method,
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
@overload
async def d3_api_aplugin(
    hostname: str, port: int, plugin_blob: dict[str, str], timeout_sec: float | None = None
) -> PluginResponse: ...


@overload
async def d3_api_aplugin(
    hostname: str, port: int, plugin_blob: TypedBlob[RetType], timeout_sec: float | None = None
) -> PluginResponse[RetType]: ...


async def d3_api_aplugin(
    hostname: str,
    port: int,
    plugin_blob: dict[str, str] | TypedBlob[RetType],
    timeout_sec: float | None = None,
) -> PluginResponse | PluginResponse[RetType]:
    # Extract blob from TypedBlob if necessary
    if isinstance(plugin_blob, TypedBlob):
        json_data = plugin_blob.json
        is_typed = True
    else:
        json_data = plugin_blob
        is_typed = False

    response: Any = await d3_api_arequest(
        Method.POST,
        hostname,
        port,
        D3_PLUGIN_ENDPOINT,
        json=json_data,
        timeout=aiohttp.ClientTimeout(timeout_sec) if timeout_sec else None,
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
    hostname: str, port: int, json: dict | None = None, timeout_sec: float | None = None
) -> Any:
    try:
        return await d3_api_arequest(
            Method.POST,
            hostname,
            port,
            D3_PLUGIN_MODULE_REG_ENDPOINT,
            json=json,
            timeout=aiohttp.ClientTimeout(timeout_sec) if timeout_sec else None,
        )
    except Exception as e:
        raise Exception(
            f"Failed to register module '{json.get('moduleName') if json else ''}': {e}"
        ) from e


###############################################################################
# API sync interface
@overload
def d3_api_plugin(
    hostname: str, port: int, plugin_blob: dict, timeout_sec: float | None = None
) -> PluginResponse: ...


@overload
def d3_api_plugin(
    hostname: str, port: int, plugin_blob: TypedBlob[RetType], timeout_sec: float | None = None
) -> PluginResponse[RetType]: ...


def d3_api_plugin(
    hostname: str,
    port: int,
    plugin_blob: dict | TypedBlob[RetType],
    timeout_sec: float | None = None,
) -> PluginResponse | PluginResponse[RetType]:
    # Extract blob from TypedBlob if necessary
    if isinstance(plugin_blob, TypedBlob):
        json_data = plugin_blob.json
        is_typed = True
    else:
        json_data = plugin_blob
        is_typed = False

    response = d3_api_request(
        Method.POST,
        hostname,
        port,
        D3_PLUGIN_ENDPOINT,
        json=json_data,
        timeout=timeout_sec if timeout_sec else None,
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
    timeout_sec: float | None = None,
) -> Any:
    try:
        return d3_api_request(
            Method.POST,
            hostname,
            port,
            D3_PLUGIN_MODULE_REG_ENDPOINT,
            json=json,
            timeout=timeout_sec if timeout_sec else None,
        )
    except Exception as e:
        raise RuntimeError(
            f"Failed to register module '{json.get('moduleName') if json else ''}': {e}"
        ) from e
