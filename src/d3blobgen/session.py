from typing import Any, Unpack

import aiohttp

from d3blobgen.api import (
    Method,
    d3_api_aplugin,
    d3_api_aregister_module,
    d3_api_arequest,
    d3_api_plugin,
    d3_api_register_module,
    d3_api_request,
)
from d3blobgen.core import D3Function
from d3blobgen.models import PluginPayload, PluginResponse, RetType


class D3SessionBase:
    def __init__(self, hostname: str, port: int, context_modules: list[str]) -> None:
        self.hostname: str = hostname
        self.port: int =  port
        self.context_modules: list[str] = context_modules


class D3Session(D3SessionBase):
    def __init__(self, hostname: str, port: int, context_modules: list[str] = []) -> None:
        super().__init__(hostname, port, context_modules)

    def __enter__(self) -> "D3Session":
        for module_name in self.context_modules:
            is_registered: bool = self.register_module(module_name)
            if not is_registered:
                raise RuntimeError(f"module {module_name} is not registered with d3function")
        return self

    def __exit__(self ,type, value, traceback) -> None:
        pass

    def rpc(self, blob: PluginPayload[RetType], timeout_sec: float | None = None) -> RetType:
        return self.plugin(blob, timeout_sec).returnValue

    def plugin(self, blob: PluginPayload[RetType], timeout_sec: float | None = None) -> PluginResponse[RetType]:
        return d3_api_plugin(self.hostname, self.port, blob, timeout_sec)

    def request(self, method: Method, url_endpoint: str, **kwargs):
        return d3_api_request(method, self.hostname, self.port, url_endpoint, **kwargs)

    def register_module(self, module_name: str, timeout_sec: float | None = None) -> bool:
        json: dict[str, str] | None = D3Function.get_module_register_payload(module_name)
        if json:
            d3_api_register_module(self.hostname, self.port, json, timeout_sec)
            return True
        return False

    def register_all_modules(self, timeout_sec: float | None = None) -> dict[str, bool]:
        modules: list[str] = [module_name for module_name in D3Function._available_d3functions.keys()]
        register_success: dict[str, bool] = {}
        for module_name in modules:
            is_registered: bool = self.register_module(module_name, timeout_sec)
            register_success[module_name] = is_registered
        return register_success


class D3AsyncSession(D3SessionBase):
    def __init__(self, hostname: str, port: int, context_modules: list[str] = []) -> None:
        super().__init__(hostname, port, context_modules)

    async def __aenter__(self) -> "D3AsyncSession":
        for module_name in self.context_modules:
            is_registered: bool = await self.register_module(module_name)
            if not is_registered:
                raise RuntimeError(f"module {module_name} is not registered with d3function")
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        pass

    async def request(self, method: Method, url_endpoint: str, **kwargs: Unpack[aiohttp.client._RequestOptions]) -> Any:
        return await d3_api_arequest(method, self.hostname, self.port, url_endpoint, **kwargs)

    async def rpc(self, blob: PluginPayload[RetType], timeout_sec: float | None = None) -> RetType:
        return (await self.plugin(blob, timeout_sec)).returnValue

    async def plugin(self, blob: PluginPayload[RetType], timeout_sec: float | None = None) -> PluginResponse[RetType]:
        return await d3_api_aplugin(self.hostname, self.port, blob, timeout_sec)

    async def register_module(self, module_name: str, timeout_sec: float | None = None):
        json: dict[str, str] | None = D3Function.get_module_register_payload(module_name)
        if json:
            await d3_api_aregister_module(self.hostname, self.port, json, timeout_sec)
            return True
        return False

    async def register_all_modules(self, timeout_sec: float | None = None) -> dict[str, bool]:
        modules: list[str] = [module_name for module_name in D3Function._available_d3functions.keys()]
        register_success: dict[str, bool] = {}
        for module_name in modules:
            is_registered: bool = await self.register_module(module_name, timeout_sec)
            register_success[module_name] = is_registered
        return register_success
