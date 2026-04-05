import serial
import time

# change to serial port name that is going to be used
ser = serial.Serial("/dev/ttyACM4", 115200, timeout=1)
time.sleep(2)

def send(cmd):
    ser.write((cmd + "\n").encode())
    print("TX:", cmd)

# Examples:
send("1")
time.sleep(3)
send("0")
send("1,60000,1000,1000")   # start flashing with parameters
