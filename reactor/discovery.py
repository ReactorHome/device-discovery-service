from netdisco.discovery import NetworkDiscovery
from threading import Thread, Event
from pyHS100 import Discover
import paho.mqtt.client as mqtt
import json
import logging

from reactor.HueService import HueService
from reactor.Outlet import Outlet
from reactor.mqtt_client import MqttClient

logging.basicConfig(level=logging.INFO)


class DeviceDiscovery(Thread):

    def __init__(self, mqtt_client: mqtt.Client):
        Thread.__init__(self)
        self._stop_event = Event()
        self.old_devices = set()
        self.dev_dict = dict()
        self.mqtt_client = mqtt_client
        self._logger = logging.getLogger("Device_Discovery")
        self.hue_service = HueService()

    def stop_thread(self):
        self._stop_event.set()

    def run(self):
        while not self._stop_event.is_set():
            self._logger.debug("loop started")
            netdis = NetworkDiscovery()

            netdis.scan()

            filter_set = {"philips_hue"}
            found_devices = set()
            discovered_devices = netdis.discover()
            devices = [a for a in discovered_devices if a in filter_set]

            if "philips_hue" in devices:
                device_info = netdis.get_info("philips_hue")
                for device in device_info:
                    if self.hue_service.bridge_registered(device["serial"]):
                        lights = self.hue_service.get_lights(device["serial"], device["host"])
                        found_devices |= set(lights)
                    self.dev_dict["philips_hue"][device["serial"]] = device["host"]

            # for dev in devices:
            #     dev_info = netdis.get_info(dev)
            #     for iDevInfo in dev_info:
            #         #found_devices.add((dev, iDevInfo["serial"], iDevInfo["host"]))
            #         if dev not in self.dev_dict:
            #             self.dev_dict[dev] = dict()
            #         self.dev_dict[dev][iDevInfo["serial"]] = iDevInfo["host"]
            netdis.stop()

            for device in Discover.discover().values():
                found_devices.add(Outlet(device.get_sysinfo(), True, device.ip_address))
                #found_devices.add(("tp-link", device.mac, device.ip_address))
                if "tp-link" not in self.dev_dict:
                    self.dev_dict["tp-link"] = dict()
                self.dev_dict["tp-link"][device.mac] = device.ip_address

            #print("new devices")
            new_connections = found_devices.difference(self.old_devices)
            #print(new_connections)
            self._logger.info("New devices: %s" % str(new_connections))


            #print("")
            #print("disconnected devices")
            disconnections = self.old_devices.difference(found_devices)
            for dis in disconnections:
                if dis[0] in self.dev_dict and dis[1] in self.dev_dict[dis[0]]:
                    del self.dev_dict[dis[0]][dis[1]]
            #print(disconnections)
            self._logger.info("Disconnected devices: %s" % str(disconnections))
            self.old_devices = found_devices.copy()

            if len(new_connections) > 0 or len(disconnections) > 0:
                message_body = json.dumps({"type": "device_connection",
                                           "hardware_id": MqttClient.hardware_id,
                                           "connections": list(new_connections),
                                           "disconnections": list(disconnections)})
                self.mqtt_client.publish("cloud_messaging", message_body)

            self._stop_event.wait(30)
