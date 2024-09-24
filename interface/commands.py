import serial
import time

#arduino_port = "/dev/cu.usbmodem34B7DA61DC282"
arduino_port = "COM13"
baud = 9600
timeout_duration = 5

commands = [
    "SET TEMP 25",
    "EMERGENCY STOP",
    "RESET",
    "REPORT"
]

try:
    ser = serial.Serial(arduino_port, baud, timeout=timeout_duration)
    print("Connected to Arduino port: " + arduino_port)
    time.sleep(2)  # Wait for Arduino to initialize

    for command in commands:
        if command:
            # Flush the input buffer before writing new data
            ser.reset_input_buffer()

            # Send the user input to the Arduino
            ser.write((command + '\n').encode('utf-8'))
            print(f"Sent command: {command}")

            time.sleep(2)

            while ser.in_waiting > 0:
                response = ser.readline().decode('utf-8').strip()
                if response:
                    print(f"Arduino responded: {response}")
            time.sleep(1)


except serial.SerialException as e:
    print(f"Error: {e}")

finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Serial port closed.")