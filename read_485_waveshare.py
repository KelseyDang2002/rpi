import sys
import time
import datetime as dt
import subprocess
from pyModbusTCP.client import ModbusClient

def get_site_id(command):
    try:
        result = subprocess.run(
            command,
            shell=isinstance(command, str),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), -1

output, error, code = get_site_id("cat /home/vsign/master/siteinfo.conf | grep '^SN' | awk '$1 ~ /^SN/ {print $1}'")
#SITE = output
SITE = "site999"
WAVESHARE = "192.168.2.151"
PORT = 502
SLAVE_ID = 43

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

client = ModbusClient(
    host=WAVESHARE,
    port=PORT,
    unit_id=SLAVE_ID,
    auto_open=True,
    auto_close=True
)

def read_register(address: int) -> float:
    regs = client.read_input_registers(address, 2)
    if regs:
        value = (regs[0] << 16) + regs[1] # combine 2 x 16-bit
        return value / 1000.0 # divide by 1000 to get true value
    else:
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
    curr_date = dt.date.today().strftime('%Y-%m-%d')
    curr_time = dt.datetime.now().strftime('%H:%M:%S')
    print(f"{curr_date} {curr_time} {str(sys.argv)}\n")

    m = get_measurements()
    data = assemble_data(curr_date, curr_time, m)
    #print(f"Final measurements: {m}")
    print(f"\nData: {data}")
    save_data_to_file(data, curr_date)
