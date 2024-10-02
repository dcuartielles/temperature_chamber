# imports
import tkinter as tk
import serial
import time


from gui_functionality import clear_entry_on_stop

window = tk.Tk()

# global variables for interaction with main
is_stopped = False
starting = False
lbl_monitor = None


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
