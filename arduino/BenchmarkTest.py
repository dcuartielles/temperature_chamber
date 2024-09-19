import serial
import time

arduino_port = "/dev/cu.usbmodem143201"
baud = 9600
timeout_duration = 5

def run_test(test_command):
    try:
        ser = serial.Serial(arduino_port, baud, timeout=timeout_duration)
        time.sleep(2)

        ser.write((test_command + '\n').encode('utf-8'))
        print(f"Sent: {test_command}")

        while True:
            if ser.in_waiting > 0:
                response = ser.readline().decode('utf-8').strip()
                print(f"Arduino: {response}")
            time.sleep(1)

    except serial.SerialException as e:
        print(f"Serial connection error: {e}")

    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial port closed.")

test_commands = [
    "RUN TEST1",
    "RUN TEST2",
    "RUN TEST3"
]

for command in test_commands:
    print(f"\nStarting {command}...")
    run_test(command)
    time.sleep(5)

