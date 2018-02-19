from netdisco.discovery import NetworkDiscovery
from threading import Thread, Event
from pyHS100 import Discover
import paho.mqtt.client as mqtt
import json

from reactor.mqtt_client import MqttClient


class DeviceDiscovery(Thread):

    def __init__(self, mqtt_client: mqtt.Client):
        Thread.__init__(self)
        self._stop_event = Event()
        self.old_devices = set()
        self.dev_dict = dict()
        self.mqtt_client = mqtt_client

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

            for dev in devices:
                dev_info = netdis.get_info(dev)
                for iDevInfo in dev_info:
                    new_devices.add((dev, iDevInfo["serial"], iDevInfo["host"]))
                    self.dev_dict[dev][iDevInfo["serial"]] = iDevInfo["host"]
            netdis.stop()

            for device in Discover.discover().values():
                new_devices.add(("tp-link", device.mac, device.ip_address))
                self.dev_dict["tp-link"][device.mac] = device.ip_address

            print("new devices")
            new_connections = new_devices.difference(self.old_devices)
            print(new_connections)

            print("")
            print("disconnected devices")
            disconnections = self.old_devices.difference(new_devices)
            for dis in disconnections:
                if dis[0] in self.dev_dict and dis[1] in self.dev_dict[dis[0]]:
                    del self.dev_dict[dis[0]][dis[1]]
            print(disconnections)
            self.old_devices = new_devices.copy()

            if len(new_connections) > 0 or len(disconnections) > 0:
                message_body = json.dumps({"type": "device_connection",
                                           "hardware_id": MqttClient.hardware_id,
                                           "connections": list(new_connections),
                                           "disconnections": list(disconnections)})
                self.mqtt_client.publish("cloud_messaging", message_body)

            self._stop_event.wait(10)
