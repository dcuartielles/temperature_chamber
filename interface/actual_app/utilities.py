import serial
import time
from concurrent.futures import ThreadPoolExecutor



def send_command(ser, command, executor):     #sends a command to arduino via serial

    if ser and ser.is_open:
        executor.submit(_send_command_task, ser, command)
    else:
        print("serial connection is not open")



def _send_command_task(ser, command):    #helper function to send the command in a background thread

    try:
        ser.reset_input_buffer()
        ser.write((command + '\n').encode('utf-8'))
        print(f"sent command: {command}") #debug line
        time.sleep(1)   #small delay for command processing
    except serial.SerialException as e:
        print(f"error sending command: {e}")
    except Exception as e:
        print(f"unexpected error in sending command: {e}")



def read_arduino_data(ser, update_callback, executor):    #reads data from arduino and updates the app's UI via a callback.

    def _read_task():

        while ser and ser.is_open:
            try:
                response = None
                if ser.in_waiting > 0:
                    response = ser.readline().decode('utf-8').strip()

                if response:
                    update_callback(f"arduino says: {response}")
                else:
                    update_callback("waiting for a word from arduino...")

                time.sleep(1)       #frequency for data to be read

            except serial.SerialException as e:
                print(f"error reading data: {e}")
                update_callback("error reading data")
                break
            except Exception as e:
                print(f"unexpected error in reading data: {e}")
                update_callback("Unexpected error")
                break

    executor.submit(_read_task)




def serial_setup(port, baudrate, timeout):          # set up serial communication
            
        try:
            ser = serial.Serial(port="COM13", baudrate=9600, timeout=5)
            print(f"connected to arduino port: {port}")
            time.sleep(1)   #make sure arduino is ready
            return ser
        except serial.SerialException as e:
            print(f"error: {e}")
            return None
        