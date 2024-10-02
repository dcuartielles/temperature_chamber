# imports
import tkinter as tk
from PIL import Image, ImageTk  # for images
import serial
import time
import json
from tkinter import messagebox, Listbox
from tkinter.filedialog import askopenfilename, asksaveasfilename


# global flag for stopping the reading process
is_stopped = False

# global flag for starting a new test sequence
starting = False

# declare listbox as it's used in functions below
listbox = None

# set up serial communication
def serial_setup(port='COM15', baudrate=9600, timeout=5, lbl_monitor=None): # adjust port if necessary
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        print(f'connected to arduino port: {port}')
        if lbl_monitor:
                lbl_monitor['text'] = f'connected to arduino port: {port}'
        time.sleep(1)  # make sure arduino is ready
        return ser
    except serial.SerialException as e:
        print(f'error: {e}')
        if lbl_monitor:
                lbl_monitor['text'] = f'error: {e}'
        return None
''' need to erase this part as it closes serial right after opening it
    finally:
            # Close serial connection
            if 'ser' in locals() and ser.is_open:
                ser.close()
                print('Serial port closed.')'''


# parse decoded serial response for smooth data extraction
'''def parse_serial_response(response):
    # split the response string into key-value pairs
    data = response.split(' | ')

    # create a dictionary to store parsed values
    parsed_data = {}

    # loop through each key-value pair and split by ':'
    for item in data:

        try:
                key, value = item.split(': ')

                # clean the key and value, and store them in dictionary
                key = key.strip()
                value = value.strip()

                # assign specific values based on key
                if key == 'Room_temp':
                    parsed_data['Room_temp'] = float(value)
                elif key == 'Desired_temp':
                    parsed_data['Desired_temp'] = float(value)
                elif key == 'Heater':
                    parsed_data['Heater'] = bool(int(value))  # convert '1' or '0' to True/False
                elif key == 'Cooler':
                    parsed_data['Cooler'] = bool(int(value))  # convert '1' or '0' to True/False
        except ValueError:
                # handle the case where splitting fails
                print(f"Could not parse item: '{item}'")
                continue  # Skip to the next item
    return parsed_data'''

ser = serial_setup()
# read data from serial
def read_data():
    global is_stopped
    global starting

    if not is_stopped:  # only read data if the system is not stopped
        if ser and ser.is_open:
            try:
                send_command(ser, 'SHOW DATA')  # send command to request data

                response = ser.readline().decode('utf-8').strip()  # decode serial response

                if response:
                    print(f'arduino responded: {response}')
                    if lbl_monitor:
                        lbl_monitor['text'] = f'{response}'

                    if response.startswith('Setting '):
                        starting = True

                else:
                    print('received unexpected message or no valid data')
                    if lbl_monitor:
                        lbl_monitor['text'] = 'received unexpected message or no valid data'

            except serial.SerialException as e:
                print(f'error reading data: {e}')
                if lbl_monitor:
                    lbl_monitor['text'] = f'error reading data: {e}'

        # schedule the next read_data call only if the system is not stopped
        window.after(1500, read_data) # run this method every 1.5 sec

# show serial updates re: running test sequence
def running_sequence():
    global is_stopped
    global starting

    if not is_stopped and starting: # run this only if system is not stopped and a new test sequence begins
        try:
            send_command(ser, 'SHOW RUNNING SEQUENCE') # send command to request running test updates

            response = ser.readline().decode('utf-8').strip() # decode serial response

            if response:
                print(f'about running sequence, arduino says: {response}')
                listbox.insert(tk.END, response)
                starting = False
            else:
                print('received unexpected message or no valid data')
        except serial.SerialException as e:
            print(f'error reading data: {e}')
            listbox.insert(tk.END, f'error reading data: {e}')


# sends a command to arduino via serial
def send_command(ser, command):
    try:
        ser.reset_input_buffer()  # clear the gates
        ser.write((command + '\n').encode('utf-8'))  # encode command in serial
        print(f'sent command: {command}')  # debug line
        time.sleep(0.02)  # small delay for command processing

    except serial.SerialException as e:
        print(f'error sending command: {e}')

    except Exception as e:
        print(f'unexpected error in sending command: {e}')


# emergency stop
def emergency_stop():
    global is_stopped
    is_stopped = True  # set flag to stop the read_data loop

    command = 'EMERGENCY STOP'
    send_command(ser, command)
    lbl_monitor['text'] = 'EMERGENCY STOP'
    clear_entry_on_stop()
    listbox.delete(0, tk.END)  # clear the listbox
    listbox.insert(0, 'EMERGENCY STOP')
