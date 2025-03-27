import serial # pip3 install pyserial
import time
import sys

BAUD = 115200

# cycling paramters by default
ON_TIME = 800
OFF_TIME = 200

# xiao = serial.Serial(port='/dev/ttyACM0', baudrate=BAUD, timeout=1) # linux
xiao = serial.Serial(port='COM3', baudrate=BAUD, timeout=1) # windows
time.sleep(1)

# prompt user for parameters
def delayParameters(on_time, off_time):
    try:
        if len(sys.argv) > 4:
            print(f"Input Error: '{sys.argv[0]}' has a maximum of 4 arguments. {len(sys.argv)} were given.")
            print("\nExiting program...")
            sys.exit(1)

        # specify on_delay and off_delay
        if len(sys.argv) == 4:
            on_delay = int(sys.argv[2]) # convert on_delay argument to int
            if on_delay > 0:
                on_time = on_delay
            else:
                print("Input Error: Only integers larger than 0 are allowed.")
                print("\nExiting program...")
                sys.exit(1)
        
            off_delay = int(sys.argv[3]) # convert off_delay argument to int
            if off_delay > 0:
                off_time = off_delay
            else:
                print("Input Error: Only integers larger than 0 are allowed.")
                print("\nExiting program...")
                sys.exit(1)
        
        # specify on_delay and use default off_delay
        if len(sys.argv) == 3:
            on_delay = int(sys.argv[2]) # convert on_delay argument to int
            if on_delay > 0:
                on_time = on_delay
            else:
                print("Input Error: Only integers larger than 0 are allowed.")
                print("\nExiting program...")
                sys.exit(1)
    
        # use default parameters if none of the conditions above apply
        print(f"Selected:\n\tOn Delay: {on_time}ms\n\tOff Delay: {off_time}ms")
        return on_time, off_time
    
    except IndexError:
        print("IndexError: List index out of range.")
        print("\nExiting program...")
        sys.exit(1)

    except ValueError:
        print("ValueError: Invalid input. Only numbers allowed.")
        print("\nExiting program...")
        sys.exit(1)
    
# turned on
def onState():
    try:
        on_delay, off_delay = delayParameters(ON_TIME, OFF_TIME)
        message = f"1,{on_delay},{off_delay}\n" 
        xiao.write(message.encode()) # tell RP2040 to turn on MOSFET
        time.sleep(1)

        response = xiao.readline().decode('utf-8').strip()
        if response:
            print(f"XIAO RP2040 says: {response}\n")

        return
    
    except TypeError:
        print("TypeError: cannot unpack non-iterable NoneType object")
        print("\nExiting program...")
        sys.exit(1)
        
# turned off
def offState():
    message = f"0\n"
    xiao.write(message.encode()) # tell RP2040 to turn off MOSFET

    response = xiao.readline().decode('utf-8').strip()
    if response:
        print(f"XIAO RP2040 says: {response}")
    return

# function to display help menu
def helpMenu():
    print("********** HELP MENU **********")
    print("\nFormat for running command via CLI:")
    print("\tpython [file.py] [action] [on_delay] [off_delay]")
    print("\n\t1 [file.py] (required)")
    print("\t\t- name of the file/program")
    print("\n\t2 [action] (required)")
    print("\t\ton - tell RP2040 microcontroller to turn on")
    print("\t\toff - tell RP2040 microcontroller to turn off")
    print("\t\thelp/h - help menu/how to run script")
    print("\n\t3 [on_delay]")
    print("\t\t- the time for LED to be turned on in milliseconds")
    print("\t\t- omit parameter to use default on delay ({ON_TIME})")
    print("\t\t- default is 800ms unless specified")
    print("\n\t4 [off_delay]")
    print("\t\t- the time for LED to be turned off in millisecondss")
    print("\t\t- omit parameter to use default off delay ({OFF_TIME})")
    print("\t\t- default is 200ms unless specified")

# function to handle command line arguments
def handleCommands():
    print(f"\nEntered: {str(sys.argv)}\n")
    
    if len(sys.argv) < 2:
        print(f"Run Error: '{sys.argv[0]}' requires at least {2 - len(sys.argv)} more command line argument.")
        print(f"Run command 'python {sys.argv[0]} help' to bring up help menu.")
        sys.exit(1)
        
    action = sys.argv[1].lower()
    if action == 'on':
        onState()
    
    elif action == 'off':
        offState()
    
    elif action == 'help' or action == 'h':
        helpMenu()
    
    else:
        print(f"Action Error: '{action}' is an invalid argument.")
        print(f"Run command 'python {sys.argv[0]} help' to bring up help menu.")
        sys.exit(1)

# main
print(f"Executing program {sys.argv[0]}...") 
handleCommands()
print("\nExiting program...")
sys.exit(0)
