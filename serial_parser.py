import serial
import time

ser = serial.Serial('COM4', 115200, timeout=1)  # Change COM3 to your port

# Send data
ser.write(b'Hello device!\n')

# Read data
while True:
    if ser.in_waiting > 0:
        print(f"Received: {ser.read(8)}")
    time.sleep(0.1)