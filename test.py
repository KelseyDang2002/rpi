import serial # pip3 install pyserial
import time
import sys

BAUD = 115200

# cycling paramters by default
ON_TIME = 800
OFF_TIME = 200
NUM_CYCLES = 100
MODE = 'c'

# xiao = serial.Serial(port='/dev/ttyACM0', baudrate=BAUD, timeout=1) # linux
xiao = serial.Serial(port='COM3', baudrate=BAUD, timeout=1) # windows
time.sleep(1)

# function to handle cycle mode or timer mode
def mode(num_cycles):
    try:
        # TODO: timer mode
        mode = sys.argv[4]
        if mode == 'cycle' or mode == 'c':
            cycles = int(sys.argv[5])
            
            # cycles = int(input("Number of cycles: "))
            if cycles == -1:
                print("Use default number of cycles")
            elif cycles > 0:
                num_cycles = cycles
            else:
                return
        
        else:
            print(f"Mode Error: '{mode}' is an invalid argument.")
            sys.exit(1)
                    
        print(f"\tNumber of cycles: {num_cycles}\n")
        return num_cycles
    
    except IndexError:
        print("IndexError: Missing a mode command line argument.")
        sys.exit(1)

# prompt user for parameters
def delayParameters(on_time, off_time):
    while True:
        try:
            
            print("Enter -1 to use default parameters.")

            on_delay = int(sys.argv[2]) # convert on_delay argument to int
            # on_delay = int(input("On delay (ms): "))
            if on_delay > 0:
                on_time = on_delay
            elif on_delay == -1:
                print("Use default on delay")
            else:
                return
            
            off_delay = int(sys.argv[3]) # convert off_delay argument to int
            # off_delay = int(input("Off delay (ms): "))
            if off_delay > 0:
                off_time = off_delay
            elif off_delay == -1:
                print("Use default off delay")
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
            
            #TODO: send num_cycles or timer limit
            
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

        on_delay, off_delay = delayParameters(ON_TIME, OFF_TIME)
        value = mode(NUM_CYCLES)
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
    print("\n\t4 [off_delay] (command line still WIP)")
    print("\t\t- the time for LED to be turned off in millisecondss")
    print("\t\t- default is 200ms unless specified")
    print("\n\t5 [mode] (required if 'on' is selected)")
    print("\t\tcycle/c")
    print("\t\t\t- the number of cycles (on and off) for the LED to flash")
    print("\t\t\t- default is 100 unless specified")
    # print("\t\t\t- either number of cycles or a timer is used, using both not allowed")
    # print("\t\ttimer/t")
    # print("\t\t\t- the amount of time for the LED to flash")
    # print("\t\t\t- default is infinite unless specified")
    # print("\t\t\t- either a timer or number of cycles is used, using both not allowed")
    # print("\t\t\t- undecided if it is seconds, minutes, hours, etc.")
    print("\n\t6 [value]")
    print("\t\t- a number either for number of cycles or amount of time")

# function to handle command line arguments
def handleCommands():
    print(f"\nEntered: {str(sys.argv)}\n")
        
    action = sys.argv[1].lower()
    
    if action == 'on':
        # TODO: takes in on_delay, off_delay, mode, and value as parameters as argv
        # if no parameters are specified, use default
        onState()
    elif action == 'off':
        offState()
    elif action == 'help' or action == 'h':
        # TODO: displays help menu on how to run program
        helpMenu()
    else:
        print(f"Action Error: '{action}' is an invalid argument.")
        sys.exit(1)
            
# main loop
while True:
    try:
        print(f"\nExecuting program {sys.argv[0]}...")
        
        # TODO: define minimum an maximum number of argument for both on state and off state
        if len(sys.argv) < 2:
            print(f"Run Error: '{sys.argv[0]}' requires {2 - len(sys.argv)} more command line argument(s).")
            sys.exit(1)
        
        handleCommands()
        print("\nExiting program...")
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\nKeyboardInterrupt: Program interrupted by user.")
        sys.exit(1)
