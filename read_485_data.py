import sys
import time
import serial
import serial.tools.list_ports
from typing import Optional

air_temperature = 0x0000
air_humidity = 0x0002
barometric_pressure = 0x0004
light_intensity = 0x0006
min_wind_direction = 0x0008
max_wind_direction = 0x000A
avg_wind_direction = 0x000C
min_wind_speed = 0x000E
max_wind_speed = 0x0010
avg_wind_speed = 0x0012
acc_rainfall = 0x0014
acc_rainfall_duration = 0x0016
rain_intensity = 0x0018
max_rainfall_intensity = 0x001A
heating_temperature = 0x001C
tilt_status = 0x001E
pm_25 = 0x0030
pm_10 = 0x0032
co2 = 0x0040
# noise_intensity = 0x0048 # not available on S1000
# global_solar_radiation = 0x004A # not available on S1000
# sunshine_duration = 0x004C # not available on S1000

registers = [
    0x0000,
    0x0002,
    0x0004,
    0x0006,
    0x0008,
    0x000A,
    0x000C,
    0x000E,
    0x0010,
    0x0012,
    0x0014,
    0x0016,
    0x0018,
    0x001A,
    0x001C,
    0x001E,
    0x0030,
    0x0032,
    0x0040,
    0x0048,
    0x004A,
    0x004C
]

def modbus_crc16(data: bytes) -> bytes:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, byteorder='little')

def build_modbus_request(slave_id: int, function_code: int, start_addr: int, quantity: int) -> bytes:
    request = bytearray()
    request.append(slave_id)
    request.append(function_code)
    request.append((start_addr >> 8) & 0xFF)
    request.append(start_addr & 0xFF)
    request.append((quantity >> 8) & 0xFF)
    request.append(quantity & 0xFF)
    request += modbus_crc16(request)
    return bytes(request)

def detect_device(port: str, baudrate: int, slave_id: int, start_addr: int) -> Optional[bytes]:
    try:
        with serial.Serial(
            port=port,
            baudrate=baudrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=2
        ) as ser:
            # print(f"Probing Slave ID {slave_id} on port {port}...")
            request = build_modbus_request(
                slave_id=slave_id,
                function_code=0x04,
                start_addr=start_addr,
                quantity=0x0020
            )
            # print(f"Request: {request}")
            # print(f"ser = {ser}")
            ser.write(request)
            response = ser.read(7)
            time.sleep(0.5)
            # print(f"Response: {response}")
            hex_string = response.hex()
            if len(response) >= 5:
                # print(f"Device responded: {hex_string}, {type(hex_string)}")
                return hex_string[-8:]
            else:
                print(f"No response from Slave ID {slave_id}.")
                return None

    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return None

if __name__ == "__main__":
    print(str(sys.argv))
    for register in registers:
        data = detect_device(port='/dev/ttyACM0', baudrate=9600, slave_id=43, start_addr=register)
        value = (int(data, 16))/1000
        print(f"Register {hex(register)} value: {value}")
