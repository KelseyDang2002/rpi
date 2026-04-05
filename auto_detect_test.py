# Macbook: conda activate meshtastic
# Both Mac and Raspberry PI: pip install meshtastic pyserial


import serial.tools.list_ports
import meshtastic.serial_interface

def find_meshtastic_device():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        # Look for ESP32/XIAO type identifiers
        if ("usbserial" in port.device or
            "usbmodem" in port.device or
            "ttyUSB" in port.device or
            "ttyAMA" in port.device):
            print(f"Found candidate device: {port.device}")
            return port.device
    raise Exception("No Meshtastic device found")

# Use detected device
port_name = find_meshtastic_device()
print(port_name)
#iface = meshtastic.serial_interface.SerialInterface(port_name)

#iface.sendText("Hello automatically detected- Z1 test 1")
