import serial
import time
import json

# Define your Arduino port and baud rate
arduino_port = "/dev/cu.usbmodem34B7DA61DC282"  # Adjust this based on your port
baud_rate = 9600
timeout_duration = 5  # Timeout for serial

# Sample JSON test (3 sequences in this case)
test_data = {
        "tests": {
            "test_1": {
                "chamber_sequences": [
                    { "temp": 60, "duration": 60000 },
                    { "temp": 65, "duration": 60000 }
                ]
            },
            "test_2": {
                "chamber_sequences": [
                    { "temp": 70, "duration": 60000 },
                    { "temp": 75, "duration": 60000 }
                ]
            }
        }
    }

# Convert the test data to a JSON string
json_test_string = json.dumps(test_data)

def send_json_to_arduino(json_data):
    try:
        # Connect to Arduino
        ser = serial.Serial(arduino_port, baud_rate, timeout=timeout_duration)
        time.sleep(2)  # Allow Arduino time to initialize
        
        # Send JSON data
        ser.write((json_data + '\n').encode('utf-8'))
        print(f"Sent to Arduino: {json_data}")

        # Continuously read Arduino output
        while True:
            if ser.in_waiting > 0:
                response = ser.readline().decode('utf-8').strip()
                print(f"Arduino: {response}")
            #time.sleep(1)

    except serial.SerialException as e:
        print(f"Serial connection error: {e}")

    finally:
        # Close serial connection
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial port closed.")

# Send the JSON test to Arduino
send_json_to_arduino(json_test_string)


