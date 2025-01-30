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
        if len(sys.argv) < 6:
            print(f"Run Error: '{sys.argv[0]}' requires {6 - len(sys.argv)} more command line argument(s).")
            sys.exit(1)
        
        print(f"Entered: {str(sys.argv)}")
        # print(f"File: {sys.argv[0]}")
        # print(f"Action: {sys.argv[1]}")
        # print(f"On Delay: {sys.argv[2]}")
        # print(f"Off Delay: {sys.argv[3]}")
        # print(f"Mode: {sys.argv[4]}")
        # print(f"Value: {sys.argv[5]}")

        command = input("\nEnter 'on' or 'off' to control sign or 'q' to quit program: ").strip().lower()

        # TODO: argc & argv implementation
        '''
        Running command via CLI:
            python [file.py] [action] [on_delay] [off_delay] [mode] [value]

            0 [file.py] (required)
                - name of the script file
            
            1 [action] (required)
                on - turn on RP2040 microcontroller
                off - turn off RP2040 microcontroller
                help - help menu/how to run script
            
            2 [on_delay]
                - the time for LED to be turned on in milliseconds
                - default is 800ms unless specified
            
            3 [off_delay]
                - the time for LED to be turned off in milliseconds
                - default is 200ms unless specified

            4 [mode]
                cycle
                    - the number of cycles (on and off) for the LED to flash
                    - default is 0 unless specified
                    - either number of cycles or a timer is used, using both not allowed
                
                timer
                    - the amount of time for the LED to flash
                    - default is infinite unless specified
                    - either a timer or number of cycles is used, using both not allowed
                    - unsure if it should be in seconds, minutes, hours, etc.

            5 [value] - a number either for number of cycles or amount of time
        '''

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
