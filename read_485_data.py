import datetime as dt
import os
import struct
import subprocess
import sys
import time
from typing import Optional

import serial


def get_site_id(command):
    try:
        result = subprocess.run(
            command,
            shell=isinstance(command, str),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), -1


output, error, code = get_site_id(
    "cat /home/vsign/master/siteinfo.conf | grep '^SN' | awk '$1 ~ /^SN/ {print $2}' | awk -F: '{print $1}'"
)
SITE = output
PORT = os.environ.get("RS485_PORT", "/dev/ttyACM0")
BR = int(os.environ.get("RS485_BAUD", "9600"))

RECORD_LABELS = [
    "site",
    "date",
    "time",
    "status",
    "avg_wind_direction_deg",
    "avg_wind_speed_m_s",
    "co2_ppm",
    "pm25_ug_m3",
    "pm10_ug_m3",
    "air_temperature_c",
    "air_humidity_pct_rh",
    "barometric_pressure_inhg",
    "reserved_1",
    "reserved_2",
    "reserved_3",
    "reserved_4",
    "reserved_5",
    "light_intensity_lx",
    "rain_intensity_mm_h",
]


registers = {
    "Air Temperature (C)": 0x0000,
    "Air Humidity (%RH)": 0x0002,
    "Barometric Pressure (Pa)": 0x0004,
    "Light Intensity (lx)": 0x0006,
    "Min Wind Direction (deg)": 0x0008,
    "Max Wind Direction (deg)": 0x000A,
    "Avg Wind Direction (deg)": 0x000C,
    "Min Wind Speed (m/s)": 0x000E,
    "Max Wind Speed (m/s)": 0x0010,
    "Avg Wind Speed (m/s)": 0x0012,
    "Accumulated Rainfall (mm)": 0x0014,
    "Accumulated Rainfall Duration (s)": 0x0016,
    "Rain Intensity (mm/h)": 0x0018,
    "Max Rainfall Intensity (mm/h)": 0x001A,
    "Heating Temperature (C)": 0x001C,
    "Tilt Status (0 or 1)": 0x001E,
    "PM2.5 (ug/m3)": 0x0030,
    "PM10 (ug/m3)": 0x0032,
    "CO2 (ppm)": 0x0040,
}

bulk_reads = (
    (0x0000, 0x0014),
    (0x0014, 0x000C),
    (0x0030, 0x0004),
    (0x0040, 0x0002),
)


def modbus_crc16(data: bytes) -> bytes:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, byteorder="little")


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


def parse_signed_32bit(register_bytes: bytes) -> float:
    raw_value = struct.unpack(">i", register_bytes)[0]
    return raw_value / 1000.0


def read_input_registers(
    ser: serial.Serial, slave_id: int, start_addr: int, quantity: int
) -> Optional[bytes]:
    request = build_modbus_request(
        slave_id=slave_id,
        function_code=0x04,
        start_addr=start_addr,
        quantity=quantity,
    )
    expected_length = 5 + (quantity * 2)

    ser.reset_input_buffer()
    ser.write(request)
    ser.flush()
    response = ser.read(expected_length)

    if len(response) != expected_length:
        print(
            f"No response or incomplete response from Slave ID {slave_id} "
            f"for start 0x{start_addr:04X}, quantity {quantity}. "
            f"Expected {expected_length} bytes, got {len(response)}."
        )
        return None

    if response[0] != slave_id or response[1] != 0x04:
        print(
            f"Unexpected Modbus header for start 0x{start_addr:04X}: "
            f"{response.hex(' ')}"
        )
        return None

    byte_count = response[2]
    if byte_count != quantity * 2:
        print(
            f"Unexpected byte count for start 0x{start_addr:04X}: "
            f"expected {quantity * 2}, got {byte_count}."
        )
        return None

    if modbus_crc16(response[:-2]) != response[-2:]:
        print(
            f"CRC mismatch for start 0x{start_addr:04X}: {response.hex(' ')}"
        )
        return None

    return response[3:-2]


def get_measurements(slave_id: int) -> list:
    measurement_values = {name: -1 for name in registers}

    try:
        with serial.Serial(
            port=PORT,
            baudrate=BR,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=2,
        ) as ser:
            for start_addr, quantity in bulk_reads:
                payload = read_input_registers(
                    ser=ser,
                    slave_id=slave_id,
                    start_addr=start_addr,
                    quantity=quantity,
                )
                if payload is None:
                    time.sleep(0.2)
                    continue

                register_map = {}
                for offset in range(0, len(payload), 2):
                    register_map[start_addr + (offset // 2)] = payload[offset : offset + 2]

                for key, address in registers.items():
                    if not (start_addr <= address < start_addr + quantity):
                        continue

                    high_word = register_map.get(address)
                    low_word = register_map.get(address + 1)
                    if high_word is None or low_word is None:
                        continue

                    measurement_values[key] = parse_signed_32bit(high_word + low_word)
                time.sleep(0.2)
    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    measurements = []
    for key in registers:
        value = measurement_values[key]
        if value == -1:
            print(f"No data received for {key}. Using -1 as placeholder.")
        else:
            print(f"{key:35s}{value}")
        measurements.append(value)

    return measurements


def assemble_data(curr_date: str, curr_time: str, measurements: list):
    print(measurements)
    data_record = []
    data_record.append(SITE)
    data_record.append(curr_date)
    data_record.append(curr_time)
    data_record.append(0)
    data_record.append(measurements[6])
    data_record.append(measurements[9])
    data_record.append(measurements[18])
    data_record.append(measurements[16])
    data_record.append(measurements[17])
    data_record.append(measurements[0])
    data_record.append(measurements[1])
    pressure_pa = int(measurements[2]) if measurements[2] != -1 else -1
    pressure = round(pressure_pa / 3386, 2) if pressure_pa != -1 else -1
    data_record.append(pressure)
    data_record.append(-1)
    data_record.append(-1)
    data_record.append(-1)
    data_record.append(-1)
    data_record.append(-1)
    data_record.append(measurements[3])
    data_record.append(measurements[12])
    return data_record


def save_data_to_file(record: list, curr_date: str, sensor_id: str):
    filename = f"/dev/shm/sensor{sensor_id}-{curr_date}.iaqm"
    try:
        with open(filename, "a") as file:
            if file.tell() == 0:
                file.write(",".join(RECORD_LABELS) + "\n")
            file.write(",".join(map(str, record)) + "\n")
    except PermissionError as e:
        print(f"Could not write to {filename}: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <slave_id> <sensor_id>")
        sys.exit(1)

    try:
        slave_id = int(sys.argv[1])
    except ValueError:
        print(f"Invalid slave ID: {sys.argv[1]!r}. It must be an integer.")
        sys.exit(1)

    sensor_id = sys.argv[2]
    date = dt.date.today()
    curr_date = date.strftime("%Y-%m-%d")
    curr_time = dt.datetime.now().strftime("%H:%M:%S")
    print(f"{curr_date} {curr_time} {str(sys.argv)} PORT: {PORT} SLAVE_ID: {slave_id}")
    m = get_measurements(slave_id)
    record = assemble_data(curr_date, curr_time, m)
    print(f"Record: {record}")
    save_data_to_file(record, curr_date, sensor_id)
