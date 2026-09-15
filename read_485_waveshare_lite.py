import sys
import argparse
import time
import datetime as dt
import subprocess
import socket
import struct

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
# SITE = "site999"
WAVESHARE = "192.168.2.151"
PORT = 502
SLAVE_ID = 43
TIMEOUT = 5.0 # seconds per connection and response
MODE = "tcp" # tcp: gateway conversion; rtu: transparent serial bridge
DEBUG = False

registers = {
    'Air Temperature (C)': 0x0000,
    'Air Humidity (%RH)': 0x0002,
    'Barometric Pressure (Pa)': 0x0004,
    'Light Intensity (lx)': 0x0006,
    'Min Wind Direction (deg)': 0x0008,
    'Max Wind Direction (deg)': 0x000A,
    'Avg Wind Direction (deg)': 0x000C,
    'Min Wind Speed (m/s)': 0x000E,
    'Max Wind Speed (m/s)': 0x0010,
    'Avg Wind Speed (m/s)': 0x0012,
    'Accumulated Rainfall (mm)': 0x0014,
    'Accumulated Rainfall Duration (s)': 0x0016,
    'Rain Intensity (mm/h)': 0x0018,
    'Max Rainfall Intensity (mm/h)': 0x001A,
    'Heating Temperature (C)': 0x001C,
    'Tilt Status (0 or 1)': 0x001E,
    'PM2.5 (ug/m3)': 0x0030,
    'PM10 (ug/m3)': 0x0032,
    'CO2 (ppm)': 0x0040
}

def recv_exact(connection, size: int, deadline: float) -> bytes:
    """Read a complete field even when TCP splits it across packets."""
    data = bytearray()
    while len(data) < size:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Modbus response timed out")
        connection.settimeout(remaining)
        try:
            chunk = connection.recv(size - len(data))
        except socket.timeout as error:
            raise TimeoutError(
                f"Timed out waiting for response field ({len(data)}/{size} bytes received)"
            ) from error
        if DEBUG and chunk:
            print(f"RX: {chunk.hex(' ')}")
        if not chunk:
            raise ConnectionError("Connection closed before the response was complete")
        data.extend(chunk)
    return bytes(data)


def modbus_crc16(data: bytes) -> bytes:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc.to_bytes(2, "little")


def read_rtu_response(connection, deadline: float) -> bytes:
    header = recv_exact(connection, 3, deadline)
    if header[0] != SLAVE_ID or header[1] not in (0x04, 0x84):
        raise ValueError(f"Unexpected RTU header: {header.hex(' ')}")
    if header[1] == 0x84:
        response = header + recv_exact(connection, 2, deadline)
    else:
        if header[2] != 4:
            raise ValueError(f"Expected 4 register bytes, got {header[2]}")
        response = header + recv_exact(connection, 6, deadline)
    if modbus_crc16(response[:-2]) != response[-2:]:
        raise ValueError("RTU response CRC mismatch")
    return response[1:-2]


def read_register(address: int, strict: bool = False) -> float:
    """Read two input registers; strict mode reports failure to diagnostic callers."""
    transaction_id = 1 # A fresh connection is used for each request.
    if MODE == "rtu":
        request = struct.pack(">BBHH", SLAVE_ID, 0x04, address, 2)
        request += modbus_crc16(request)
    else:
        request = struct.pack(">HHHBBHH", transaction_id, 0, 6, SLAVE_ID, 0x04, address, 2)
    stage = "connecting"
    try:
        with socket.create_connection((WAVESHARE, PORT), timeout=TIMEOUT) as connection:
            stage = "sending request"
            deadline = time.monotonic() + TIMEOUT
            if DEBUG:
                print(f"Connected to {WAVESHARE}:{PORT}; mode={MODE}; slave={SLAVE_ID}")
                print(f"TX: {request.hex(' ')}")
            connection.sendall(request)
            stage = "receiving response"
            if MODE == "rtu":
                response = read_rtu_response(connection, deadline)
            else:
                header = recv_exact(connection, 7, deadline)
                response_id, protocol_id, length, unit_id = struct.unpack(">HHHB", header)
                if (response_id != transaction_id or protocol_id != 0
                        or unit_id != SLAVE_ID):
                    raise ValueError(f"Unexpected Modbus TCP header: {header.hex(' ')}")
                if not 2 <= length <= 254:
                    raise ValueError("Invalid Modbus response length")
                response = recv_exact(connection, length - 1, deadline)
            if response[0] == 0x84:
                if len(response) != 2:
                    raise ValueError("Malformed Modbus exception response")
                raise ValueError(f"Modbus exception code {response[1]}")
            if len(response) != 6 or response[:2] != bytes((0x04, 4)):
                raise ValueError("Invalid input-register response")
            high, low = struct.unpack(">HH", response[2:])
            return ((high << 16) + low) / 1000.0
    except (OSError, ValueError) as error:
        print(f"Read failed at register 0x{address:04X} while {stage}: {error}")
        if strict:
            raise
        return -1


def get_measurements() -> list:
    measurements = []
    for key, addr in registers.items():
        val = read_register(addr)
        if val == -1:
            print(f"No data for {key}. Using -1 as placeholder.")
        else:
            print(f"{key:35s}{val}")
        measurements.append(val)
    return measurements

def assemble_data(curr_date: str, curr_time: str, measurements: list):
    data_record = []
    data_record.append(SITE) # [0] site number
    data_record.append(curr_date) # [1] date
    data_record.append(curr_time) # [2] time
    data_record.append(0) # [3] zero (no usage)
    data_record.append(measurements[4]) # [4] avg wind direction
    data_record.append(measurements[9]) # [5] avg wind speed
    data_record.append(measurements[18]) # [6] co2
    data_record.append(measurements[16]) # [7] pm2.5
    data_record.append(measurements[17]) # [8] pm10
    data_record.append(measurements[0]) # [9] temperature
    data_record.append(measurements[1]) # [10] relative humidity
    pressure_pa = int(measurements[2])
    pressure_inhg = pressure_pa / 3386
    pressure = round(pressure_inhg, 2)
    data_record.append(pressure) # [11] pressure
    data_record.append(-1) # [12] co (-1 as placeholder)
    data_record.append(-1) # [13] no (-1)
    data_record.append(-1) # [14] no2 (-1)
    data_record.append(-1) # [15] o3 (-1)
    data_record.append(-1) # [16] so2 (-1)
    data_record.append(measurements[3]) # [17] light intensity
    data_record.append(measurements[13]) # [18] rainfall intensity
    return data_record

def save_data_to_file(record: list, curr_date: str):
    filename = f"/dev/shm/{SITE}-{curr_date}.iaqm"
    with open(filename, 'a') as file:
        file.write(','.join(map(str, record)) + '\n')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Package-free Waveshare weather sensor reader")
    parser.add_argument("--mode", choices=("tcp", "rtu"), default=MODE,
                        help="tcp for Modbus TCP-to-RTU gateway; rtu for transparent TCP bridge")
    parser.add_argument("--host", default=WAVESHARE)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--slave-id", type=int, default=SLAVE_ID)
    parser.add_argument("--timeout", type=float, default=TIMEOUT)
    parser.add_argument("--probe", action="store_true", help="Read temperature once without saving a record")
    parser.add_argument("--debug", action="store_true", help="Print sent and received bytes")
    args = parser.parse_args()
    if not 1 <= args.slave_id <= 247 or not 1 <= args.port <= 65535:
        parser.error("slave-id must be 1..247 and port must be 1..65535")
    if not 0 < args.timeout < float("inf"):
        parser.error("timeout must be a positive finite number")
    MODE, WAVESHARE, PORT = args.mode, args.host, args.port
    SLAVE_ID, TIMEOUT, DEBUG = args.slave_id, args.timeout, args.debug
    if args.probe:
        try:
            print(f"Air Temperature (C): {read_register(0x0000, strict=True)}")
        except (OSError, ValueError):
            sys.exit(1)
        except KeyboardInterrupt:
            sys.exit(130)
        sys.exit(0)
    curr_date = dt.date.today().strftime('%Y-%m-%d')
    curr_time = dt.datetime.now().strftime('%H:%M:%S')
    print(f"{curr_date} {curr_time} {str(sys.argv)}\n")

    try:
        m = get_measurements()
    except KeyboardInterrupt:
        print("\nReading cancelled.")
        sys.exit(130)
    data = assemble_data(curr_date, curr_time, m)
    #print(f"Final measurements: {m}")
    print(f"\nData: {data}")
    save_data_to_file(data, curr_date)
