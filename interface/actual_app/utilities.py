import serial
import time



def send_command(ser, command, executor):     #sends a command to arduino via serial

    if ser and ser.is_open:
        executor.submit(_send_command_task, ser, command)



def _send_command_task(ser, command):    #helper function to send the command in a background thread

    try:
        ser.reset_input_buffer()
        ser.write((command + '\n').encode('utf-8'))
        print(f"sent command: {command}")
        time.sleep(1)
    except serial.SerialException as e:
        print(f"error sending command: {e}")



def read_arduino_data(ser, update_callback):    #reads data from arduino and updates the app's UI via a callback.

    while ser and ser.is_open:
        try:
            response = None
            if ser.in_waiting > 0:
                response = ser.readline().decode('utf-8').strip()

            if response:
                update_callback(f"arduino says: {response}")
            else:
                update_callback("waiting for a word from arduino...")

            time.sleep(1)

        except serial.SerialException as e:
            print(f"error reading data: {e}")
            update_callback("error reading data")
            break