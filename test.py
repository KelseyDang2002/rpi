import serial # pip3 install pyserial
import time
import sys

BAUD = 115200

# cycling paramters by default
ON_TIME = 800
OFF_TIME = 200
NUM_CYCLES = 100
TIME_LIMIT = 0

# xiao = serial.Serial(port='/dev/ttyACM0', baudrate=BAUD, timeout=1) # linux
xiao = serial.Serial(port='COM3', baudrate=BAUD, timeout=1) # windows
time.sleep(1)

# function to handle cycle mode or timer mode
def mode(num_cycles, time_limit):
    try:
        mode = sys.argv[4].lower()
        if mode == 'cycle' or mode == 'c':
            cycles = int(sys.argv[5])
            
            # cycles = int(input("Number of cycles: "))
            if cycles > 0:
                num_cycles = cycles
            elif cycles == -1:
                num_cycles
            else:
                return
            print(f"\tNumber of cycles: {num_cycles}\n")
            return num_cycles
            
        # elif mode == 'timer' or mode == 't':
        #     timer = int(sys.argv[5])

        #     if timer >= 0:
        #         time_limit = timer
        #     elif timer == -1:
        #         time_limit
        #     else:
        #         return
        #     print(f"\tTime Limit: {time_limit}\n")
        #     time_limit = time.sleep(time_limit)
        #     return time_limit
        
        else:
            print(f"Mode Error: '{mode}' is an invalid argument.")
            sys.exit(1)
    
    except IndexError:
        print("IndexError: Missing a mode command line argument.")
        sys.exit(1)

# prompt user for parameters
def delayParameters(on_time, off_time):
    while True:
        try:
            on_delay = int(sys.argv[2]) # convert on_delay argument to int
            # on_delay = int(input("On delay (ms): "))
            if on_delay > 0:
                on_time = on_delay
            elif on_delay == -1:
                on_time
            else:
                return
            
            off_delay = int(sys.argv[3]) # convert off_delay argument to int
            # off_delay = int(input("Off delay (ms): "))
            if off_delay > 0:
                off_time = off_delay
            elif off_delay == -1:
                on_time
            else:
                return
            
            print(f"Selected:\n\tOn Delay: {on_time}ms\n\tOff Delay: {off_time}ms")
            return on_time, off_time
        
        except IndexError:
            print(f"IndexError: Missing on_delay or off_delay arguments.")
            sys.exit(1)

        except ValueError:
            print("ValueError: Invalid input. Only numbers allowed.")
            sys.exit(1)

        except KeyboardInterrupt:
            print("\n\nKeyboardInterrupt: Program interrupted by user.")
            break

# function for flashing LED
def flash(on_delay, off_delay, value):
    print("Calling flash function...\n")
    
    # TODO: might have to make infintie loop
    for i in range(value):
        try:
            xiao.write(b'0')
            time.sleep(off_delay / 1000)
            # TODO: send off delay to RP2040
            
            xiao.write(b'1')
            time.sleep(on_delay / 1000)
            # TODO: send on delay to RP2040
            
            # TODO: send num_cycles
            
            print(f"{i + 1} cycle(s) completed")

        except KeyboardInterrupt:
            print("\n\nKeyboardInterrupt: Program interrupted by user.")
            break
    return
    
# turned on
def onState():
    try:
        xiao.write(b'1') # tell RP2040 to turn on MOSFET
        time.sleep(1)

        response = xiao.readline().decode('utf-8').strip()
        if response:
            print(f"XIAO RP2040 says: {response}\n")

        # TODO: check what 3rd param is
        # if cycle or timer, it is mode
        # if number, on_delay
        # check what 4th param is
        # if cycle or timer, it is mode
        # if number, off_delay
        # check param after mode is specified
        # if empty, default, otherwise it is specified
        # separate function to check on params
        on_delay, off_delay = delayParameters(ON_TIME, OFF_TIME)
        value = mode(NUM_CYCLES, TIME_LIMIT)
        flash(on_delay, off_delay, value)
        return
    
    except TypeError:
        print("TypeError: cannot unpack non-iterable NoneType object")
        print("\nExiting program...")
        sys.exit(1)
        
# turned off
def offState():
    xiao.write(b'0') # tell RP2040 to turn off MOSFET

    response = xiao.readline().decode('utf-8').strip()
    if response:
        print(f"XIAO RP2040 says: {response}")
    return

def helpMenu():
    print("********** HELP MENU **********")
    print("\nFormat for running command via CLI:")
    print("\tpython [file.py] [action] [on_delay] [off_delay] [mode] [value]")
    print("\n\t1 [file.py] (required)")
    print("\t\t- name of the script file")
    print("\n\t2 [action] (required)")
    print("\t\ton - tell RP2040 microcontroller to turn on")
    print("\t\toff - tell RP2040 microcontroller to turn off")
    print("\t\thelp/h - help menu/how to run script")
    print("\n\t3 [on_delay] (command line still WIP)")
    print("\t\t- the time for LED to be turned on in milliseconds")
    print("\t\t- default is 800ms unless specified")
    print("\t\t- enter -1 to use default")
    print("\n\t4 [off_delay] (command line still WIP)")
    print("\t\t- the time for LED to be turned off in millisecondss")
    print("\t\t- default is 200ms unless specified")
    print("\t\t- enter -1 to use default")
    print("\n\t5 [mode] (required if 'on' is selected)")
    print("\t\tcycle/c")
    print("\t\t\t- the number of cycles (on and off) for the LED to flash")
    print("\t\t\t- default is 100 unless specified")
    print("\t\t\t- enter -1 to use default")
    # print("\t\t\t- either number of cycles or a timer is used, using both not allowed")
    # print("\t\ttimer/t")
    # print("\t\t\t- the amount of time for the LED to flash")
    # print("\t\t\t- default is infinite unless specified")
    # print("\t\t\t- either a timer or number of cycles is used, using both not allowed")
    # print("\t\t\t- undecided if it is seconds, minutes, hours, etc.")
    print("\n\t6 [value]")
    print("\t\t- a number either for number of cycles or amount of time")
    print("\t\t- use default values if not specified")

# function to handle command line arguments
def handleCommands():
    print(f"\nEntered: {str(sys.argv)}\n")
    
    if len(sys.argv) < 2:
        print(f"Run Error: '{sys.argv[0]}' requires at least {2 - len(sys.argv)} more command line argument.")
        print(f"Run command 'python {sys.argv[0]} help' to bring up help menu.")
        sys.exit(1)
        
    action = sys.argv[1].lower()
    if action == 'on':
        # TODO: takes in on_delay, off_delay, mode, and value as parameters as argv
        # if no parameters are specified, use default
        if len(sys.argv) < 6:
            print(f"Run Error: '{sys.argv[0]}' requires {6 - len(sys.argv)} more command line argument(s).")
            print(f"Run command 'python {sys.argv[0]} help' to bring up help menu.")
            sys.exit(1)
        
        onState()
    
    elif action == 'off':
        offState()
    
    elif action == 'help' or action == 'h':
        helpMenu()
    
    else:
        print(f"Action Error: '{action}' is an invalid argument.")
        print(f"Run command 'python {sys.argv[0]} help' to bring up help menu.")
        sys.exit(1)
            
# main loop
while True:
    try:
        print(f"\nExecuting program {sys.argv[0]}...") 
        handleCommands()
        print("\nExiting program...")
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\nKeyboardInterrupt: Program interrupted by user.")
        sys.exit(1)
