import sys
import time
import datetime as dt
import serial
from typing import Optional

PORT = '/dev/ttyACM0'
BR = 9600
ID = 43

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

reg = [
    0x0000, # air temperature
    0x0002, # air humidity
    0x0004, # pressure
    0x0006, # light intensity
    0x00CA, # avg wind direction
    0x0012, # avg wind speed
    0x0018, # rainfall intensity
    0x0040, # co2
    0x0030, # pm2.5
    0x0032, # pm10
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

def get_modbus_response(port: str, baudrate: int, slave_id: int, start_addr: int) -> Optional[bytes]:
    try:
        with serial.Serial(
            port=port,
            baudrate=baudrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=2
        ) as ser:
            request = build_modbus_request(
                slave_id=slave_id,
                function_code=0x04,
                start_addr=start_addr,
                quantity=0x0020
            )
            ser.write(request)
            response = ser.read(7)
            time.sleep(0.5) # 500ms delay
            hex_string = response.hex() # convert response to hex string

            # if we recieve a response back
            if len(response) >= 5:
                return hex_string[-8:]
            else:
                print(f"No response from device with Slave ID {slave_id}.")
                return None

    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return None

def get_measurements() -> list:
    # loop through register addresses
    measurements = []
    for key, value in registers.items():
        data = get_modbus_response(port=PORT, baudrate=BR, slave_id=ID, start_addr=value)
        data = (int(data, 16)) / 1000
        measurements.append(data)
        print(f"{key:35s}{data}")
    return measurements

def assemble_data(curr_date: str, curr_time: str, measurements: list):
    print(measurements)
    data_record = []
    data_record.append('site21') # [0] site number
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
    data_record.append(measurements[2]) # [11] pressure
    data_record.append(-1) # [12] co (-1 as placeholder)
    data_record.append(-1) # [13] no (-1)
    data_record.append(-1) # [14] no2 (-1)
    data_record.append(-1) # [15] o3 (-1)
    data_record.append(-1) # [16] so2 (-1)
    data_record.append(measurements[3]) # [17] light intensity
    data_record.append(measurements[13]) # [18] rainfall intensity
    return data_record

def save_data_to_file(record: list):
    with open('/dev/shm/test.txt', 'a') as file:
        file.write(','.join(map(str, record)) + '\n')

if __name__ == "__main__":
    date = dt.date.today()
    curr_date = date.strftime('%Y-%m-%d')
    curr_time = dt.datetime.now().strftime('%H:%M:%S')
    print(f"{curr_date} {curr_time} {str(sys.argv)}")
    m = get_measurements()
    record = assemble_data(curr_date, curr_time, m)
    print(f"Record: {record}")
    save_data_to_file(record)
