import serial # pip3 install pyserial
import serial.tools.list_ports
import time
import sys

BAUD = 115200

# paramters by default
TIMEOUT = 60000 # 1 minute
ON_TIME = 1000
OFF_TIME = 1000

# xiao = serial.Serial(port='/dev/ttyACM0', baudrate=BAUD, timeout=1) # linux
xiao = serial.Serial(port='COM3', baudrate=BAUD, timeout=1) # windows
time.sleep(1)

# prompt user for parameters
def delayParameters(timeout, on_time, off_time):
    try:
        if len(sys.argv) > 5:
            print(f"Input Error: '{sys.argv[0]}' has a maximum of 5 arguments. {len(sys.argv)} were given.")
            print("\nExiting program...")
            sys.exit(1)

        # specify time_out, on_delay and off_delay
        if len(sys.argv) == 5:
            time_out = int(sys.argv[2]) # convert time_out argument to int
            if time_out > 0:
                timeout = time_out
            else:
                print("Input Error: Only integers larger than 0 are allowed.")
                print("\nExiting program...")
                sys.exit(1)
            
            on_delay = int(sys.argv[3]) # convert on_delay argument to int
            if on_delay > 0:
                on_time = on_delay
            else:
                print("Input Error: Only integers larger than 0 are allowed.")
                print("\nExiting program...")
                sys.exit(1)

            off_delay = int(sys.argv[4]) # convert off_delay argument to int
            if off_delay > 0:
                off_time = off_delay
            else:
                print("Input Error: Only integers larger than 0 are allowed.")
                print("\nExiting program...")
                sys.exit(1)
                
        # specify time_out, on_delay, and use default off_delay
        if len(sys.argv) == 4:
            time_out = int(sys.argv[2]) # convert on_delay argument to int
            if time_out > 0:
                timeout = time_out
            else:
                print("Input Error: Only integers larger than 0 are allowed.")
                print("\nExiting program...")
                sys.exit(1)
                
            on_delay = int(sys.argv[3]) # convert on_delay argument to int
            if on_delay > 0:
                on_time = on_delay
            else:
                print("Input Error: Only integers larger than 0 are allowed.")
                print("\nExiting program...")
                sys.exit(1)
        
        # specify time_out and use default on_delay and off_delay
        if len(sys.argv) == 3:
            time_out = int(sys.argv[2]) # convert on_delay argument to int
            if time_out > 0:
                timeout = time_out
            else:
                print("Input Error: Only integers larger than 0 are allowed.")
                print("\nExiting program...")
                sys.exit(1)
    
        # use default parameters if none of the conditions above apply
        print(f"Selected:\n\tTimeout: {timeout}ms\n\tOn Delay: {on_time}ms\n\tOff Delay: {off_time}ms")
        return timeout, on_time, off_time
    
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
        timeout, on_delay, off_delay = delayParameters(TIMEOUT, ON_TIME, OFF_TIME)
        message = f"1,{timeout}, {on_delay},{off_delay}\n" 
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
    print("\n\t3 [timeout]")
    print("\t\t- the time it takes for flashing to turn off after the on command")
    print("\t\t- omit parameter to use default timeout")
    print(f"\t\t- default is {TIMEOUT}ms unless specified")
    print("\n\t4 [on_delay]")
    print("\t\t- the time for LED to be turned on in milliseconds")
    print("\t\t- omit parameter to use default on delay")
    print(f"\t\t- default is {ON_TIME}ms unless specified")
    print("\n\t5 [off_delay]")
    print("\t\t- the time for LED to be turned off in millisecondss")
    print("\t\t- omit parameter to use default off delay")
    print(f"\t\t- default is {OFF_TIME}ms unless specified")

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
if __name__ == "__main__":
    print(f"Executing program {sys.argv[0]}...")
    
    ports = serial.tools.list_ports.comports()
    print("\nConnected COM Ports:")
    for port, desc, hwid in sorted(ports):
        print(f"\t{port}: {desc} [{hwid}]")
    
    handleCommands()
    print("\nExiting program...")
    sys.exit(0)
