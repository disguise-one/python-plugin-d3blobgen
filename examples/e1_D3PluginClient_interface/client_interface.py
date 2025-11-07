import json

from d3blobgen.client import D3PluginClient
from typing import TypedDict, TYPE_CHECKING
if TYPE_CHECKING:
    from d3blobgen.scripts.d3 import *


def print_title(title: str):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


class Surface(TypedDict):
    name: str
    uid: int
    time: str


class MyCustomPlugin(D3PluginClient):
    def __init__(self, hostname, port):
        super().__init__(hostname, port)
        self.my_id: int = 0
        
    def sleep_50ms(self) -> str:
        import time
        time.sleep(0.05)
        return "after 50ms"

    def my_time(self) -> str:
        import datetime
        return str(datetime.datetime.now())
    
    def my_time_with_note(self, note: str) -> str:
        return "time: {}, note: {}".format(self.my_time(), note)
    
    def get_my_id(self) -> int:
        return self.my_id
    
    def set_my_id(self, new_id: int):
        self.my_id = new_id

    def get_surface_uid_with_time(self, surface_name: str) -> dict[str, str]:
        surface: Screen2 = resourceManager.load(
            Path('objects/screen2/{}.apx'.format(surface_name)),
            Screen2
        )
        return {
            "name": surface.path.filename,
            "uid": str(surface.uid),
            "time": self.my_time()
        }

    def get_typed_surface(self, surface_name: str) -> Surface:
        surface: Screen2 = resourceManager.load(
            Path('objects/screen2/{}.apx'.format(surface_name)),
            Screen2
        )
        return {
            "name": surface.path.filename,
            "uid": surface.uid,
            "time": self.my_time()
        }

    def rename_surface(self, surface_name: str, new_surface_name: str):
        surface: Screen2 = resourceManager.load(
            Path('objects/screen2/{}.apx'.format(surface_name)),
            Screen2
        )
        surface.rename(surface.path.replaceFilename(new_surface_name))


def main():
    DESIGNER_IP = "localhost"
    DESIGNER_PORT = 80

    print_title("Client class module to register")
    client_to_visualise = MyCustomPlugin(DESIGNER_IP, DESIGNER_PORT)
    print("Blob:")
    print(json.dumps(client_to_visualise.get_register_module_blob(), indent=2))
    print("\nContents:")
    print(client_to_visualise.get_register_module_content())

    print_title("Client class module examples")
    with MyCustomPlugin(DESIGNER_IP, DESIGNER_PORT) as client:
        print("1. get persist state of MyCustomPlugin")
        my_id: int = client.get_my_id()
        print(f"id: {my_id}")

        print("2. update persist state of MyCustomPlugin")
        client.set_my_id(2)
        my_id: int = client.get_my_id()
        print(f"id: {my_id}")

        print("3. sleep 50ms")
        result: str = client.sleep_50ms()
        print(f"- result: {result}")

        print("4. get current time")
        current_time: str = client.my_time()
        print(f"- result: {current_time}")

        print("5. get current time with note")
        time_with_note: str = client.my_time_with_note(note="test note")
        print(f"- result: {time_with_note}")

        print("6. get surface uid with time")
        surface_with_time: dict[str, str] = client.get_surface_uid_with_time(surface_name="surface 1")
        print(surface_with_time)

        print("7. get typed surface")
        typed_surface = client.get_typed_surface(surface_name="surface 1")
        print(typed_surface)

        print("8. rename surface")
        client.rename_surface(surface_name="surface 1", new_surface_name="surface 2")
        surface_with_time = client.get_surface_uid_with_time(surface_name="surface 2")
        print(surface_with_time)
        client.rename_surface(surface_name="surface 2", new_surface_name="surface 1")
        surface_with_time = client.get_surface_uid_with_time(surface_name="surface 1")
        print(surface_with_time)

if __name__ == "__main__":
    main()

