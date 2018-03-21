from reactor.TPLinkService import TPLinkService
from reactor.discovery import DeviceDiscovery
from reactor.mqtt_client import MqttClient

if __name__ == '__main__':
    mqtt_client = MqttClient()
    device_discovery_thread = DeviceDiscovery(mqtt_client.get_client())
    mqtt_client.set_discover(device_discovery_thread)
    device_discovery_thread.start()
    try:
        mqtt_client.start()
    except (KeyboardInterrupt, Exception) as e:
        mqtt_client.disconnect()
        device_discovery_thread.stop_thread()

