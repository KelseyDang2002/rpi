import serial # pip3 install pyserial
import time
import sys

BAUD = 115200

# cycling paramters by default
ON_TIME = 800
OFF_TIME = 200
NUM_CYCLES = 100

# xiao = serial.Serial(port='/dev/ttyACM0', baudrate=BAUD, timeout=1) # linux
xiao = serial.Serial(port='COM3', baudrate=BAUD, timeout=1) # windows
time.sleep(1)

# prompt user for parameters
def promptParameters(on_time, off_time, num_cycles):
    while True:
        try:
            print("Enter -1 to use default parameters.")

            on_delay = int(input("On delay (ms): "))
            if on_delay > 0:
                on_time = on_delay
            elif on_delay == -1:
                print("Use default on delay")
            else:
                return
            
            off_delay = int(input("Off delay (ms): "))
            if off_delay > 0:
                off_time = off_delay
            elif off_delay == -1:
                print("Use default off delay")
            else:
                return
            
            cycles = int(input("Number of cycles: "))
            if cycles > 0:
                num_cycles = cycles
            elif cycles == -1:
                print("Use default number of cycles")
            else:
                return
            
            print(f"Selected:\n\tOn delay: {on_time}ms\n\tOff_delay: {off_time}ms\n\tCycles: {num_cycles}\n")
            return on_time, off_time, num_cycles

        except ValueError:
            print("ValueError: Invalid input. Only numbers allowed.")

        except KeyboardInterrupt:
            print("\n\nKeyboardInterrupt: Program interrupted by user.")
            break

# function for flashing LED
def flash(on_delay, off_delay, num_cycles):
    print("Calling flash function...\n")
    
    # TODO: experiment with timer
    for i in range(num_cycles):
        try:
            xiao.write(b'0')
            time.sleep(off_delay / 1000)
            # TODO: send off delay to RP2040
            
            xiao.write(b'1')
            time.sleep(on_delay / 1000)
            # TODO: send on delay to RP2040
            
            print(f"{i + 1} cycle(s) completed")

        except KeyboardInterrupt:
            print("\n\nKeyboardInterrupt: Program interrupted by user.")
            break
    return
    
# turned on
def onState():
    try:
        xiao.write(b'1') # tell RP2040 to turn on MOSFET

        response = xiao.readline().decode('utf-8').strip()
        if response:
            print(f"XIAO RP2040 says: {response}\n")

        on_delay, off_delay, num_cycles = promptParameters(ON_TIME, OFF_TIME, NUM_CYCLES)
        flash(on_delay, off_delay, num_cycles)
        return
    
    except TypeError:
        print("TypeError: cannot unpack non-iterable NoneType object")
        return
        
# turned off
def offState():
    xiao.write(b'0') # tell RP2040 to turn off MOSFET

    response = xiao.readline().decode('utf-8').strip()
    if response:
        print(f"XIAO RP2040 says: {response}")
    return

# main loop
while True:
    try:
        command = input("\nEnter 'on' or 'off' to control sign or 'q' to quit program: ").strip().lower()

        # TODO: argv implementation
        if command == "on":
            onState()
        elif command == "off":
            offState()
        elif command == "q":
            print("\nExiting program...")
            sys.exit(0)
        else:
            print("Invalid command. Try again.")
        
    except KeyboardInterrupt:
        print("\n\nKeyboardInterrupt: Program interrupted by user.")
