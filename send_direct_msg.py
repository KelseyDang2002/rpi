# Macbook: conda activate meshtastic
# Both Mac and Raspberry PI: pip install meshtastic pyserial
# In Mac: Found candidate device: /dev/cu.usbmodem983DAE61358C1

# To do: Check ACK.
# To do: Make proper class structure so that it can be used from other files.

#!/usr/bin/env python3
import time
import sys
from typing import Optional

# pip install meshtastic pyserial
import serial.tools.list_ports
import meshtastic.serial_interface


TARGET_LONG = "Meshtastic 97c0"   # device you want to DM
TARGET_SHORT = "ITS1"                   # fallback short name
MESSAGE = "This is 8fa8 from python"

def find_serial_port() -> str:
    """
    Try to let Meshtastic auto-detect; if that fails, fall back to scanning.
    Tested. Works on macOS (/dev/tty.usbserial*, /dev/tty.usbmodem*) and Linux (/dev/ttyUSB*, /dev/ttyACM*).
    """
    try:
        # Let the library auto-detect first
        meshtastic.serial_interface.SerialInterface().close()
        return None  # library will auto-pick when we pass no devPath
    except Exception:
        pass

    # Manual scan fallback
    candidates = []
    for p in serial.tools.list_ports.comports():
        d = p.device
        if any(tag in d for tag in ("usbserial", "usbmodem", "ttyUSB", "ttyACM")):
            candidates.append(d)
    if not candidates:
        raise RuntimeError("No Meshtastic serial ports found.")
    # Prefer ttyUSB/ttyACM on Linux, otherwise take the first
    candidates.sort(key=lambda x: ("ttyUSB" not in x and "ttyACM" not in x, x))
    return candidates[0]

def wait_for_nodes(iface, timeout=25):
    """Wait until the node database arrives so we can resolve names."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        if getattr(iface, "nodesByNum", None):
            if len(iface.nodesByNum) > 0:
                return True
        time.sleep(0.3)
    return False

def find_node_id_by_name(iface, long_name: str, short_name: str) -> Optional[str]:
    """Return node 'user.id' like '!abcdef12' that matches long or short name."""
    if not iface.nodesByNum:
        return None
    for node in iface.nodesByNum.values():
        user = node.get("user", {})
        if user.get("longName") == long_name or user.get("shortName") == short_name:
            return user.get("id")
    return None

def main():
    dev = find_serial_port()  # None means "let library auto-detect"
    iface = meshtastic.serial_interface.SerialInterface(devPath=dev) if dev else meshtastic.serial_interface.SerialInterface()

    if not wait_for_nodes(iface):
        iface.close()
        raise RuntimeError("Timed out waiting for node list. Make sure the target is on the same channel and heard recently.")

    target_id = find_node_id_by_name(iface, TARGET_LONG, TARGET_SHORT)
    if not target_id:
        iface.close()
        raise RuntimeError(f"Could not find node with long='{TARGET_LONG}' or short='{TARGET_SHORT}'. Try sending a ping from the app so it appears.")

    # Direct (unicast) message by destinationId
    iface.sendText(MESSAGE, destinationId=target_id, wantAck=True)
    print(f"Sent DM to {TARGET_SHORT or TARGET_LONG} ({target_id}): {MESSAGE}")

    iface.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
