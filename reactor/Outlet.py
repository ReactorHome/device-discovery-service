

class Outlet:
    def __init__(self, hw_info, connected, connection_address):
        self.type = 1
        self.hardware_id = hw_info["mac"]
        self.connected = connected
        self.name = hw_info["alias"]
        self.manufacturer = "TP-Link"
        self.connection_address = connection_address
        self.model = hw_info["model"]
        self.on = True if hw_info["relay_state"] == 1 else False

    def __hash__(self):
        return hash(self.connected) ^ \
               hash(self.manufacturer) ^ \
               hash(self.model) ^ \
               hash(self.hardware_id) ^ \
               hash(self.name) ^ \
               hash(self.on) ^ \
               hash((self.connected, self.model, self.manufacturer, self.hardware_id, self.name, self.on))

    def __eq__(self, other):
        return (self.connected, self.model, self.manufacturer, self.hardware_id, self.name, self.on) == \
            (other.connected, other.model, other.manufacturer, other.hardware_id, other.name, other.on)
