import json
import asyncio

from d3blobgen.client import D3PluginClient
from typing import TypedDict, TYPE_CHECKING
if TYPE_CHECKING:
    from d3blobgen.scripts.d3 import *


class Surface(TypedDict):
    name: str
    uid: int
    time: str


class MyCustomAsyncPlugin(D3PluginClient):
    def __init__(self, hostname, port):
        super().__init__(hostname, port)
        self.my_id: int = 0
        
    async def sleep_50ms(self) -> str:
        import time
        time.sleep(0.05)
        return "after 50ms"

    async def my_time(self) -> str:
        import datetime
        return str(datetime.datetime.now())
    
    async def my_time_with_note(self, note: str) -> str:
        return "time: {}, note: {}".format(self.my_time(), note)
    
    async def get_my_id(self) -> int:
        return self.my_id
    
    async def set_my_id(self, new_id: int):
        self.my_id = new_id

    async def get_surface_uid_with_time(self, surface_name: str) -> dict[str, str]:
        surface: Screen2 = resourceManager.load(
            Path('objects/screen2/{}.apx'.format(surface_name)),
            Screen2
        )
        return {
            "name": surface.path.filename,
            "uid": str(surface.uid),
            "time": self.my_time()
        }

    async def get_typed_surface(self, surface_name: str) -> Surface:
        surface: Screen2 = resourceManager.load(
            Path('objects/screen2/{}.apx'.format(surface_name)),
            Screen2
        )
        return {
            "name": surface.path.filename,
            "uid": surface.uid,
            "time": self.my_time()
        }

    async def rename_surface(self, surface_name: str, new_surface_name: str):
        surface: Screen2 = resourceManager.load(
            Path('objects/screen2/{}.apx'.format(surface_name)),
            Screen2
        )
        surface.rename(surface.path.replaceFilename(new_surface_name))


def print_title(title: str):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


async def main():
    DESIGNER_IP = "localhost"
    DESIGNER_PORT = 80

    print_title("Client class module to register")
    client_to_visualise = MyCustomAsyncPlugin(DESIGNER_IP, DESIGNER_PORT)
    print("Blob:")
    print(json.dumps(client_to_visualise.get_register_module_blob(), indent=2))
    print("\nContents:")
    print(client_to_visualise.get_register_module_content())

    print_title("Client class module examples")
    async with MyCustomAsyncPlugin(DESIGNER_IP, DESIGNER_PORT) as client:
        print("1. get persist state of MyCustomPlugin")
        my_id: int = await client.get_my_id()
        print(f"id: {my_id}")

        print("2. update persist state of MyCustomPlugin")
        await client.set_my_id(2)
        my_id: int = await client.get_my_id()
        print(f"id: {my_id}")

        print("3. sleep 50ms")
        result: str = await client.sleep_50ms()
        print(f"- result: {result}")

        print("4. get current time")
        current_time: str = await client.my_time()
        print(f"- result: {current_time}")

        print("5. get current time with note")
        time_with_note: str = await client.my_time_with_note(note="test note")
        print(f"- result: {time_with_note}")

        print("6. get surface uid with time")
        surface_with_time: dict[str, str] = await client.get_surface_uid_with_time(surface_name="surface 1")
        print(surface_with_time)

        print("7. get typed surface")
        typed_surface = await client.get_typed_surface(surface_name="surface 1")
        print(typed_surface)

        print("8. rename surface")
        await client.rename_surface(surface_name="surface 1", new_surface_name="surface 2")
        surface_with_time = await client.get_surface_uid_with_time(surface_name="surface 2")
        print(surface_with_time)
        await client.rename_surface(surface_name="surface 2", new_surface_name="surface 1")
        surface_with_time = await client.get_surface_uid_with_time(surface_name="surface 1")
        print(surface_with_time)


if __name__ == "__main__":
    asyncio.run(main())
