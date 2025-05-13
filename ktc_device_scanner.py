from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
from time import sleep

# https://github.com/python-zeroconf/python-zeroconf/blob/master/examples/registration.py
class MyListener(ServiceListener):

    def __init__(self) -> None:
        super().__init__()
        self.device_info = []

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        # print(f"Service {name} updated")
        pass

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        # print(f"Service {name} removed")
        pass

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        # print(f"Service {name} added, service info: {info}")
        self.device_info.append(info)

def main():
    zeroconf = Zeroconf()
    listener = MyListener()
    browser = ServiceBrowser(zeroconf, "_ktcdevice._tcp.local.", listener)
    sleep(5) # to get all devices in network - or TODO: find a way to call zeroconf.close later
    zeroconf.close()
    return listener.device_info

if __name__ == '__main__':
    main()
