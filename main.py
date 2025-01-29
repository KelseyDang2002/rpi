import serial # pip3 install pyserial
import time
import sys

BAUD = 115200

# cycling paramters by default
ON_TIME = 800
OFF_TIME = 200

# xiao = serial.Serial(port='/dev/ttyACM0', baudrate=BAUD, timeout=1) # linux
xiao = serial.Serial(port='COM3', baudrate=BAUD, timeout=1) # windows
time.sleep(2)

def control_state(state):
    if state == "on":
        xiao.write(b'1') # tell RP2040 to turn on MOSFET
    
    elif state == "off":
        xiao.write(b'0') # tell RP2040 to turn off MOSFET

    else:
        print("Invalid state.")

def parameters(on_time, off_time):
    on_delay = int(input("On delay (ms) (enter -1 to use default): "))
    off_delay = int(input("Off delay (ms) (enter -1 to use default): "))
    num_cycles = int(input("Number of cycles: "))

    if on_delay > 0:
        on_time = on_delay
    elif on_delay == -1:
        print(f"Default: {on_time} ms")
    else:
        return False
    
    if off_delay > 0:
        off_time = off_delay
    elif off_delay == -1:
        print(f"Default: {off_time} ms")
    else:
        return False
    
    if num_cycles < 0:
        return False

    return on_delay, off_delay, num_cycles

def flash(on_time, off_time, num_cycles):
    print("Calling flash function...")

    # convert params to string before sending to RP2040
    for i in range(num_cycles):
        xiao.write(b'0')
        print("Light Off")
        xiao.write(str(off_time).encode()) # send on delay to RP2040

        xiao.write(b'1')
        print("Light On")
        xiao.write(str(on_time).encode()) # send off delay to RP2040

while True:
    try:
        command = input("Enter 'on' or 'off' to control sign: ").strip()
        control_state(command)

        response = xiao.readline().decode('utf-8').strip()
        if response:
            print(f"XIAO RP2040 says: {response}")

        # XIAO sends byte back to RPi
        incomingChar = xiao.read().decode('utf-8')
        if incomingChar == '0':
            print(f"XIAO write: {incomingChar}")

        elif incomingChar == '1':
            print(f"XIAO write: {incomingChar}")
            
            on_time, off_time, num_cycles = parameters(ON_TIME, OFF_TIME)

            flash(on_time, off_time, num_cycles)

        else:
            print("No incoming char.")
            break
        
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user.")
        sys.exit()
