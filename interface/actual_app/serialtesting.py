import serial

ser = serial.Serial("COM13", baudrate=9600, timeout=1)
while True:
    if ser.in_waiting > 0:
        response = ser.readline().decode('utf-8').strip()
        print(f"Received: {response}")
