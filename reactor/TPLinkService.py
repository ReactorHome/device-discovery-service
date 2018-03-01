import logging
import json

from pyHS100 import SmartPlug


class TPLinkService:
    def __init__(self):
        self._logger = logging.getLogger("TPLinkService")

    def handle(self, outlet_ip, json_message):
        self._logger.info("TP-Link handle called")
        message = json.loads(json_message)
        plug = SmartPlug(outlet_ip)
        plug.turn_on() if message["on"] else plug.turn_off()
        self._logger.info("Device with ip %s turned on %s" % (outlet_ip, message["on"]))
