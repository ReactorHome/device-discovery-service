from time import sleep

from reactor.discovery import DeviceDiscovery
from reactor.mqtt_client import MqttClient

if __name__ == '__main__':
    mqtt_client = MqttClient()
    device_discovery_thread = DeviceDiscovery()
    device_discovery_thread.start()
    try:
        mqtt_client.start()
    except KeyboardInterrupt:
        mqtt_client.disconnect()
        print("client disconnected")
    device_discovery_thread.stop_thread()