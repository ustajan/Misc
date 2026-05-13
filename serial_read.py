'''
Generic python script for opening and readin a serial port.
'''


import serial
import sys

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <serial_port>")
    print("Example:")
    print(f"  {sys.argv[0]} /dev/cu.usbmodem2101")
    sys.exit(1)

PORT = sys.argv[1]
BAUD = 115200
TIMEOUT = 1

try:
    ser = serial.Serial(PORT, BAUD, timeout=TIMEOUT)
except serial.SerialException as e:
    print(f"Failed to open serial port {PORT}: {e}")
    sys.exit(1)

print(f"Connected to {PORT} at {BAUD} baud")
print("Waiting for data...\n")

try:
    while True:
        data = ser.readline()
        if data:
            print(data.decode("utf-8", errors="replace"), end="")
except KeyboardInterrupt:
    print("\nExiting.")
finally:
    ser.close()
