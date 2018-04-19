import logging
import json

import os
import getpass
from pathlib import Path

from reactor_hue.hue.HueApiClient import HueApiClient


class HueService:
    def __init__(self):
        self.home = str(Path.home())
        self._logger = logging.getLogger("HueService")
        self._logger.info(self.home)
        self._logger.info(getpass.getuser())
        self._logger.info(os.environ['HOME'])
        self.bridges = None
        self._read_json_bridge_file()
        self.keys_to_remove = ["id", "type", "hardware_id", "connected", "name", "manufacturer", "connection_address", "model", "supports_color", "internal_id"]

    def handle(self, bridge_ip, json_message):
        self._logger.info("Handling mqtt message")
        self._logger.debug(json_message)
        api_client = HueApiClient(bridge_ip, "reactor-home", None)
        internal_id = json_message["internal_id"]
        for key in json_message.copy():
            if key in self.keys_to_remove:
                del json_message[key]
        json_response = api_client.update_light_state(internal_id, json_message)
        self._logger.info("Update light response: " + json.dumps(json_message))

    def register_bridge(self, bridge_ip, json_message):
        self._logger.info("Registering hubs")
        api_client = HueApiClient("http://"+bridge_ip, "reactor-home", None)
        if self.bridges is None or json_message["hardware_id"] not in self.bridges:
            response, code = api_client.register()
            self._logger.info(response)
            if code:
                if self.bridges is None:
                    self.bridges = dict()
                self.bridges[json_message["hardware_id"]] = response
                self._write_json_bridge_file()
            return code
        else:
            return True

    def _read_json_bridge_file(self):
        if os.path.isfile(self.home + "/.reactor/hue-bridges.json"):
            with open(self.home + "/.reactor/hue-bridges.json", "r") as json_file:
                json_string = json_file.read()
                self.bridges = json.loads(json_string)
        else:
            self.bridges = None

    def _write_json_bridge_file(self):
        if not os.path.isdir(self.home + "/.reactor"):
            os.mkdir(self.home + "/.reactor")
        with open(self.home + "/.reactor/hue-bridges.json", "w") as json_file:
            json_file.write(json.dumps(self.bridges))

    def get_lights(self, serial, bridge_ip):
        username = self.bridges[serial]
        api_client = HueApiClient(bridge_ip, "reactor-home", username)
        return api_client.get_lights()

    def bridge_registered(self, bridge_serial):
        if self.bridges is None:
            return False
        return True if bridge_serial in self.bridges else False
