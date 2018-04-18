from reactor.HueService import HueService
from reactor.TPLinkService import TPLinkService
from reactor.discovery import DeviceDiscovery
from reactor.mqtt_client import MqttClient

if __name__ == '__main__':
    hs = HueService()
    mqtt_client = MqttClient(hs)
    device_discovery_thread = DeviceDiscovery(mqtt_client.get_client(), hs)
    mqtt_client.set_discover(device_discovery_thread)
    device_discovery_thread.start()
    try:
        mqtt_client.start()
    except (KeyboardInterrupt, Exception) as e:
        print(e)
        mqtt_client.disconnect()
        device_discovery_thread.stop_thread()

