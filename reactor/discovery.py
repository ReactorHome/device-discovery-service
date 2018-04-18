import sys
from netdisco.discovery import NetworkDiscovery
from threading import Thread, Event
from pyHS100 import Discover, SmartPlug
import paho.mqtt.client as mqtt
import json
import logging

from reactor_hue.hue.HueBridge import HueBridge
from reactor_hue.hue.HueLight import HueLight

from reactor.HueService import HueService
from reactor.Outlet import Outlet
from reactor.mqtt_client import MqttClient


class DeviceDiscovery(Thread):

    def __init__(self, mqtt_client: mqtt.Client, hs):
        Thread.__init__(self)
        self._stop_event = Event()
        self.old_devices = set()
        self.dev_dict = dict()
        self.new_hue_bridges = set()
        self.mqtt_client = mqtt_client
        self._logger = logging.getLogger("Device_Discovery")
        self.hue_service = hs

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
            _new_hue_bridges = set()
            _bridge_names = dict()
            discovered_devices = netdis.discover()
            devices = [a for a in discovered_devices if a in filter_set]

            _dev_dict[1] = dict()
            if "philips_hue" in devices:
                device_info = netdis.get_info("philips_hue")
                for device in device_info:
                    # if self.hue_service.bridge_registered(device["serial"]):
                    #     lights = self.hue_service.get_lights(device["serial"], "http://"+device["host"])
                    #     found_devices |= set(lights)
                    #if 1 not in _dev_dict:
                    _dev_dict[1][device["serial"]] = device["host"]
                    _bridge_names[device["serial"]] = device["name"]
            netdis.stop()

            _dev_dict[0] = dict()
            for device in Discover.discover().values():
                #self._logger.info(json.dumps(device.get_sysinfo()))
                # found_devices.add(Outlet(device.get_sysinfo(), True, device.ip_address))
                #if 0 not in _dev_dict:
                _dev_dict[0][device.mac] = device.ip_address

            _dev_dict[2] = dict()
            if 1 in _dev_dict:
                for serial, host in _dev_dict[1].items():
                    if self.hue_service.bridge_registered(serial):
                        lights = self.hue_service.get_lights(serial, host)
                        found_devices |= set(lights)
                        for light in lights:
                            _dev_dict[2][light.hardware_id] = host
                    else:
                        _new_hue_bridges.add(HueBridge(_bridge_names[serial], serial))

            if 0 in _dev_dict:
                for serial, host in _dev_dict[0].items():
                    outlet = SmartPlug(host)
                    found_devices.add(Outlet(outlet.get_sysinfo(), True, outlet.ip_address))

            new_connections = found_devices.difference(self.old_devices)
            self._logger.info("New devices: %s" % json.dumps([ob.__dict__ for ob in list(new_connections)]))

            disconnections = self.old_devices.difference(found_devices)

            for dev in disconnections:
                if dev.hardware_id not in _dev_dict[0] and dev.hardware_id not in _dev_dict[2]:
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
                #self.mqtt_client.publish("cloud_messaging", message_body)

            new_bridges = _new_hue_bridges.difference(self.new_hue_bridges)
            self.new_hue_bridges = _new_hue_bridges
            self._logger.info("Detected Bridges: %s" % json.dumps([ob.__dict__ for ob in list(new_bridges)]))

            if len(new_bridges) > 0:
                message_body = json.dumps({
                    "type": "bridge_message",
                    "hardware_id": MqttClient.hardware_id,
                    "data": [ob.__dict__ for ob in list(new_bridges)]
                })
                #self.mqtt_client.publish("cloud_messaging", message_body)

            self._stop_event.wait(5)
