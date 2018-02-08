from netdisco.discovery import NetworkDiscovery
from threading import Thread, Event


class DeviceDiscovery(Thread):

    def __init__(self):
        Thread.__init__(self)
        self._stop_event = Event()
        self.old_devices = set()

    def stop_thread(self):
        self._stop_event.set()

    def run(self):
        while not self._stop_event.is_set():
            print("loop started")
            netdis = NetworkDiscovery()

            netdis.scan()

            filter_set = {"philips_hue"}
            new_devices = set()
            found_devices = netdis.discover()
            devices = [a for a in found_devices if a in filter_set]
            #print(devices)

            for dev in devices:
                devInfo = netdis.get_info(dev)
                for iDevInfo in devInfo:
                    new_devices.add((dev, iDevInfo["serial"], iDevInfo["host"]))

            print("new devices")
            print(new_devices.difference(self.old_devices))

            print("")
            print("disconnected devices")
            print(self.old_devices.difference(new_devices))
            self.old_devices = new_devices.copy()

            # for dev in netdis.discover():
            #     print(dev)

            netdis.stop()
