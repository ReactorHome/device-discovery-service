import sys
from netdisco.discovery import NetworkDiscovery
from threading import Thread, Event
from pyHS100 import Discover, SmartPlug
import paho.mqtt.client as mqtt
import json
import logging

from reactor_hue.hue.HueLight import HueLight

from reactor.HueService import HueService
from reactor.Outlet import Outlet
from reactor.mqtt_client import MqttClient


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
            _dev_dict = dict()
            discovered_devices = netdis.discover()
            devices = [a for a in discovered_devices if a in filter_set]

            if "philips_hue" in devices:
                device_info = netdis.get_info("philips_hue")
                for device in device_info:
                    # if self.hue_service.bridge_registered(device["serial"]):
                    #     lights = self.hue_service.get_lights(device["serial"], "http://"+device["host"])
                    #     found_devices |= set(lights)
                    if "philips_hue" not in _dev_dict:
                        _dev_dict["philips_hue"] = dict()
                    _dev_dict["philips_hue"][device["serial"]] = device["host"]
            netdis.stop()

            for device in Discover.discover().values():
                #self._logger.info(json.dumps(device.get_sysinfo()))
                # found_devices.add(Outlet(device.get_sysinfo(), True, device.ip_address))
                if "tp-link" not in _dev_dict:
                    _dev_dict["tp-link"] = dict()
                _dev_dict["tp-link"][device.mac] = device.ip_address

            if "philips_hue" in _dev_dict:
                for serial, host in _dev_dict["philips_hue"].items():
                    if self.hue_service.bridge_registered(serial):
                        lights = self.hue_service.get_lights(serial, "http://"+host)
                        found_devices |= set(lights)

            if "tp-link" in _dev_dict:
                for serial, host in _dev_dict["tp-link"].items():
                    outlet = SmartPlug(host)
                    found_devices.add(Outlet(outlet.get_sysinfo(), True, outlet.ip_address))

            new_connections = found_devices.difference(self.old_devices)
            self._logger.info("New devices: %s" % json.dumps([ob.__dict__ for ob in list(new_connections)]))

            disconnections = self.old_devices.difference(found_devices)

            for dev in disconnections:
                dev.connected = False
                new_connections.add(dev)

            self._logger.info("Disconnected devices: %s" % json.dumps([ob.__dict__ for ob in list(disconnections)]))
            self.old_devices = found_devices.copy()
            self.dev_dict = _dev_dict.copy()

            if len(new_connections) > 0 or len(disconnections) > 0:
                # message_body = json.dumps({"type": "device_connection",
                #                            "hardware_id": MqttClient.hardware_id,
                #                            "connections": [ob.__dict__ for ob in list(new_connections)],
                #                            "disconnections": [ob.__dict__ for ob in list(disconnections)]})
                message_body = json.dumps({"type": "state_change",
                                           "hardware_id": MqttClient.hardware_id,
                                           "state_change_list": [ob.__dict__ for ob in list(new_connections)]})
                self.mqtt_client.publish("cloud_messaging", message_body)

            self._stop_event.wait(30)
