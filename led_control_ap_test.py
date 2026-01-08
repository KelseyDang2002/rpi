import socket
import requests
import time
import sys

ESP32_IP = "10.42.0.100"
ESP32_PORT = 4210

# parameters by default
TIMEOUT = 10000
ON_TIME = 1000
OFF_TIME = 1000

def parameters(timeout, on_time, off_time):
    try:
        if len(sys.argv) > 5:
            print(f"Input Error: '{sys.argv[0]}' has a maximum of 5 arguments. {                                                                                                             len(sys.argv)} were given.")
            print("\nExiting program...")
            sys.exit(1)

        # specify time_out, on_delay, and off_delay
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

# send commands via UDP
def send_udp(message: str):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5.0)
    try:
        sock.sendto(message.encode(), (ESP32_IP, ESP32_PORT))
        try:
            data, _ = sock.recvfrom(1024)
            print(f"XIAO says: ", data.decode())
        except socket.timeout:
            print("No response (timeout)")
    finally:
        sock.close()

def onState():
    timeout, on_delay, off_delay = parameters(TIMEOUT, ON_TIME, OFF_TIME)
    message = f"1,{timeout},{on_delay},{off_delay}"
    send_udp(message)
    # session = requests.Session()
    # response = session.get(f"http://{ESP32_IP}/ledon?timeout={timeout}&high={o                                                                                                             n_delay}&low={off_delay}")
    # if response:
    #     print(f"XIAO says: {response.text}")
    # else:
    #     print("No response.")
    # return

def offState():
    message = "0"
    send_udp(message)
    # session = requests.Session()
    # response = session.get(f"http://{ESP32_IP}/ledoff")
    # if response:
    #     print(f"XIAO says: {response.text}")
    # else:
    #     print(f"No response.")
    # return

def helpMenu():
    print("********** HELP MENU **********")
    print("\nFormat for running command via CLI:")
    print("\tpython [file.py] [action] [timeout] [on_delay] [off_delay]")
    print("\n\t1 [file.py] (required)")
    print("\t\t- name of the file/program")
    print("\n\t2 [action] (required)")
    print("\t\ton - tell XIAO microcontroller to turn on")
    print("\t\toff - tell XIAO microcontroller to turn off")
    print("\t\thelp/h - help menu/how to run script")
    print("\n\t3 [timeout]")
    print("\t\t- the time it takes for flashing to turn off after the on command                                                                                                             ")
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

def handleCommands():
    print(f"\nEntered: {str(sys.argv)}\n")

    if len(sys.argv) < 2:
        print(f"Run Error: '{sys.argv[0]}' requires at least {2 - len(sys.argv)}                                                                                                              more command line argument.")
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

if __name__ == "__main__":
    print(f"\nExecuting program {sys.argv[0]}...")
    handleCommands()
    print(f"\nExiting program...")
    sys.exit(0)
