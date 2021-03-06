import ssl

import paho.mqtt.client as mqtt
import netifaces
import json
import platform
import logging

from reactor import TPLinkService
#from reactor.discovery import DeviceDiscovery
from reactor.HueService import HueService

if platform.system() == "Darwin":
    addr = "en0"
else:
    addr = "eth0"


class MqttClient:
    hardware_id = netifaces.ifaddresses(addr)[netifaces.AF_LINK][0]["addr"]
    #hardware_id = "b8:27:eb:a7:c2:3e"

    def __init__(self, hs):
        self.client = mqtt.Client(transport="tcp")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.tls_set(ca_certs=None,
                            certfile=None,
                            keyfile=None,
                            cert_reqs=ssl.CERT_REQUIRED,
                            tls_version=ssl.PROTOCOL_TLS,
                            ciphers=None)
        self.message_handlers = {
            0: TPLinkService().handle,
            1: hs.register_bridge,
            2: hs.handle
        }
        self.discover = None
        self._logger = logging.getLogger("MqttClient")

    def set_discover(self, discover):
        self.discover = discover

    def get_client(self):
        return self.client

    def start(self):
        self.client.connect("message-broker.myreactorhome.com", 1883, 45)

        # Blocking call that processes network traffic, dispatches callbacks and
        # handles reconnecting.
        # Other loop*() functions are available that give a threaded interface and a
        # manual interface.
        self.client.loop_forever()

    def disconnect(self):
        self.client.publish("cloud_messaging", "{\"type\":\"disconnection\","
                                               "\"hardware_id\": \"" + MqttClient.hardware_id + "\"}")
        self.client.disconnect()

    # The callback for when the client receives a CONNACK response from the server.
    @staticmethod
    def on_connect(client: mqtt.Client, userdata, flags, rc):
        print("Connected with result code " + str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe("$SYS/#")
        client.subscribe(MqttClient.hardware_id)
        client.publish("cloud_messaging", "{\"type\":\"connection\","
                                          "\"hardware_id\": \"" + MqttClient.hardware_id + "\"}")
        client.will_set("cloud_messaging", "{\"type\":\"disconnection\","
                                           "\"hardware_id\": \"" + MqttClient.hardware_id + "\"}")

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client: mqtt.Client, userdata, msg):
        self._logger.info("Received message")
        message = msg.payload.decode("utf-8")
        self._logger.info("Message: " + message)
        json_dict = json.loads(message)
        #self._logger.info(message)
        # if "message_type" in json_dict:
        #     if json_dict["message_type"] == "register-bridge":
        #         self.message_handlers[1]("", json_dict["host"])
        # else:
        device_address = self.get_device_address(json_dict)
        if device_address is not None:
            self._logger.info("Device Address: " + device_address)
            self.message_handlers[json_dict['type']](device_address, json_dict['device'])
            #print(msg.topic + " " + msg.payload.decode("utf-8"))

    def get_device_address(self, json_message):
        if json_message['type'] in self.discover.dev_dict and \
                json_message['device']['hardware_id'] in self.discover.dev_dict[json_message['type']]:
            return self.discover.dev_dict[json_message['type']][json_message['device']['hardware_id']]

        return None
