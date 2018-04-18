import logging
import json

import os
from pathlib import Path

from reactor_hue.hue.HueApiClient import HueApiClient


class HueService:
    def __init__(self):
        self.home = str(Path.home())
        self._logger = logging.getLogger("HueService")
        self.bridges = None
        self._read_json_bridge_file()

    def handle(self, bridge_ip, json_message):
        self._logger.info("Handling mqtt message")
        self._logger.debug(json_message)
        api_client = HueApiClient(bridge_ip, "reactor-home", None)

    def register_bridge(self, bridge_ip, json_message):
        self._logger.info("Registering hubs")
        api_client = HueApiClient(bridge_ip, "reactor-home", None)
        response, code = api_client.register()
        if code:
            if self.bridges is None:
                self.bridges = dict()
            self.bridges[json_message["hardware_id"]] = response
            self._write_json_bridge_file()
        return code

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
