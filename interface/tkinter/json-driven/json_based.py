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


###############        FUNCTIONALITY AND LOGIC       ###############

#### JSON HANDLING ####

# send json through serial / run all tests
def send_json_to_arduino(test_data):
    json_data = json.dumps(test_data)  # convert py dictionary to json

    ser.write((json_data + '\n').encode('utf-8'))
    print(f'sent to Arduino: {json_data}')

    # Continuously read Arduino output
    while True:
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8').strip()
            print(f'Arduino: {response}')
        # time.sleep(1)


# open json file and convert it to py dictionary
def open_file():
    # open a file
    filepath = 'C:/Users/owenk/OneDrive/Desktop/Arduino/temperature chamber/temperature_chamber/interface/tkinter/json-driven/test_data.json'

    try:
        with open(filepath, mode='r') as input_file:
            test_data = json.load(input_file)  # convert raw json to py dictionary
            custom = test_data.get('custom', [])  # get the 'custom' list
            for i, step in enumerate(custom):
                step['duration'] = step['duration'] / 60000  # convert minutes to miliseconds for arduino
            return test_data  # return py dictionary

    except FileNotFoundError:
        print(f'file {filepath} not found')
        return None


# clear out any old custom test from file at the beginning of the session:
def clear_out_custom():
    test_data = open_file()
    # check if the 'custom' key exists and reset it to an empty list
    if 'custom' in test_data:
        test_data['custom'] = []  # keep the key but clear its contents

    save_file(test_data)  # save the updated dictionary back to the JSON file
    return test_data  # return the Python dictionary


# save input dictionary to json file
def save_file(test_data):
    filepath = 'C:/Users/owenk/OneDrive/Desktop/Arduino/temperature chamber/temperature_chamber/interface/tkinter/json-driven/test_data.json'

    custom = test_data.get('custom', [])  # get the 'custom' list

    for i, step in enumerate(custom):
        step['duration'] = step['duration'] * 60000  # convert minutes to miliseconds for arduino

    try:

        # write to a file
        with open(filepath, 'w') as f:
            # convert dictionary to json and write
            json.dump(test_data, f, indent=4)
            print(f'data saved to {filepath}')

    except Exception as e:
        print(f'failed to save file: {e}')


# add a step to the custom test
def add_step():
    test_data = open_file()

    if test_data is not None:
        # get input and clear it of potential empty spaces
        temp_string = ent_temp.get().strip()
        duration_string = ent_duration.get().strip()

        # initialize temp and duration
        temp = None
        duration = None
        is_valid = True  # track overall validity

        if temp_string:
            try:
                temp = float(temp_string)
                if temp >= 100:
                    print('max 100')
                    ent_temp.delete(0, tk.END)  # clear the entry
                    ent_temp.insert(0, 'max temperature = 100°C')  # show error message in entry
                    is_valid = False

            except ValueError:
                print('numbers only')
                ent_temp.delete(0, tk.END)  # clear the entry
                ent_temp.insert(0, 'numbers only')  # show error message in entry
                is_valid = False
        else:
            print('no temperature input')
            ent_temp.delete(0, tk.END)  # clear the entry
            ent_temp.insert(0, 'enter a number')  # show error message in entry
            is_valid = False

        if duration_string:
            try:
                duration = int(duration_string)
                if duration < 1:  # check for a minimum duration 
                    print('minimum duration is 1 minute')
                    ent_duration.delete(0, tk.END)
                    ent_duration.insert(0, 'minimum duration is 1 minute')
                    is_valid = False
            except ValueError:
                print('numbers only')
                ent_duration.delete(0, tk.END)  # clear the entry
                ent_duration.insert(0, 'numbers only')  # show error message in entry
                is_valid = False
        else:
            print('no valid duration')
            ent_duration.delete(0, tk.END)  # clear the entry
            ent_duration.insert(0, 'enter a number')  # show error message in entry
            is_valid = False

            # check if both entries are valid before proceeding
        if is_valid and temp is not None and duration is not None:
            new_sequence = {'temp': temp, 'duration': duration}
            test_data = open_file()
            test_data['custom'].append(new_sequence)
            save_file(test_data)
            update_listbox()
        else:
            print('cannot add custom test due to invalid inputs.')

    else:
        print('unable to add custom test due to file loading error')


# remove the selected step from the custom test
def remove_step():
    try:
        selected_index = listbox.curselection()[0]  # get the selected step index
        test_data = open_file()
        del test_data['custom'][selected_index]  # remove the selected step
        save_file(test_data)
        update_listbox()  # update the listbox display
    except IndexError:
        messagebox.showwarning('warning', 'no step selected to remove!')


# modify the selected step
def modify_step():
    try:
        selected_index = listbox.curselection()[0]
        temp = float(ent_temp.get().strip())
        duration = int(ent_duration.get().strip())
        test_data = open_file()
        test_data['custom'][selected_index] = {'temp': temp, 'duration': duration}
        save_file(test_data)
        update_listbox()
    except IndexError:
        messagebox.showwarning('warning', 'no step selected to modify!')
    except ValueError:
        messagebox.showwarning('warning', 'invalid input!')


# update the listbox to show the current steps
def update_listbox():
    listbox.delete(0, tk.END)  # clear current listbox
    test_data = open_file()
    for i, step in enumerate(test_data['custom']):
        listbox.insert(tk.END, f'step {i + 1}: temp = {step["temp"]}°C, duration = {step["duration"]} mins')


# add custom test
def add_custom():
    test_data = open_file()

    if test_data is not None:
        save_file(test_data)  # save back to json file
        print('custom test added successfully')
        ent_temp.delete(0, tk.END)  # clear the temp entry
        ent_duration.delete(0, tk.END)  # clear the duration entry
        listbox.insert(0, 'custom test uploaded')


# run all benchmark tests (test_1, test_2, test_3) automatically
def run_all_benchmark():
    test_data = open_file()
    global starting

    if test_data is not None:

        listbox.delete(0, tk.END)
        ent_temp.delete(0, tk.END)
        ent_duration.delete(0, tk.END)

        # filter out the benchmark test keys (those that start with 'test_')
        benchmark_tests = [key for key in test_data.keys() if key.startswith('test_')]

        # iterate through each benchmark test and run it
        for test_key in benchmark_tests:
            test = test_data.get(test_key, [])

            if test:  # if the test data is available
                send_json_to_arduino(test)  # send the data to Arduino

                # print status and update the listbox
                print(f'Running {test_key}')
                starting = True
                window.after(1500, running_sequence)
            else:
                print(f'{test_key} not found')
                listbox.insert(0, f'{test_key} not found')

    else:
        # handle case when no test data is found
        print('no test data found on file')
        listbox.insert(0, 'no test data found on file')


# choose and run one test
def pick_your_test(test_choice):
    test_data = open_file()
    global starting

    if test_data is not None:

        # clear out listbox & entries
        listbox.delete(0, tk.END)
        ent_temp.delete(0, tk.END)
        ent_duration.delete(0, tk.END)

        # handle the test choice
        if test_choice == 'test 1':
            test_1 = test_data.get('test_1', [])
            send_json_to_arduino(test_1)
            starting = True
            window.after(1500, running_sequence)
        elif test_choice == 'test 2':
            test_2 = test_data.get('test_2', [])
            send_json_to_arduino(test_2)
            starting = True
            window.after(1500, running_sequence)
        elif test_choice == 'test 3':
            test_3 = test_data.get('test_3', [])
            send_json_to_arduino(test_3)
            starting = True
            window.after(1500, running_sequence)
        else:
            custom_test = test_data.get('custom', [])
            send_json_to_arduino(custom_test)
            starting = True
            window.after(1500, running_sequence)
    else:
        print('no such test on file')
        listbox.insert(0, 'no such test on file')


def run_all_tests():
    test_data = open_file()
    global starting

    if test_data is not None:

        all_tests = [key for key in test_data.keys()]

        # clear out listbox & entries
        listbox.delete(0, tk.END)
        ent_temp.delete(0, tk.END)
        ent_duration.delete(0, tk.END)

        # iterate through each test test and run it
        for test_key in all_tests:
            test = test_data.get(test_key, [])

            if test:  # if the test data is available
                send_json_to_arduino(test)  # send the data to Arduino
                # print status and update the listbox
                print(f'running {test_key}')
                starting = True
                window.after(1500, running_sequence)
            else:
                print(f'{test_key} not found')
                listbox.insert(0, f'{test_key} not found or empty')

    else:
        # handle case when no test data is found
        print('no test data found on file')
        listbox.delete(0, tk.END)
        listbox.insert(0, 'no test data found on file')


#### INTERFACE FUNCTIONALITY ####

# function to clear the entry widget
def clear_entry_on_click(event):
    if event.widget.get() in ['temperature in °C: ', 'numbers only', 'duration in minutes: ', 'max temperature = 100°C',
                              'enter a number',
                              'minimum duration is 1 minute']:  # check for placeholder or warning text
        event.widget.delete(0, tk.END)  # clear the entry widget
        event.widget['fg'] = 'black'  # change text color to normal if needed


def clear_entry_on_stop():
    ent_duration.delete(0, tk.END)
    ent_temp.delete(0, tk.END)


def add_placeholder(entry, placeholder_text):
    entry.insert(0, placeholder_text)
    entry['fg'] = 'grey'  # set the color to a lighter grey for the placeholder text

    def on_focus_in(event):
        if entry.get() == placeholder_text:
            entry.delete(0, tk.END)  # Clear the placeholder text when focused
            entry['fg'] = 'black'  # Set the text color to normal

    def on_focus_out(event):
        if entry.get() == '':  # If the user didn't type anything, put the placeholder back
            entry.insert(0, placeholder_text)
            entry['fg'] = 'grey'

    # bind the events
    entry.bind('<FocusIn>', on_focus_in)
    entry.bind('<FocusOut>', on_focus_out)


#### SERIAL INTERACTION ####

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

# Non-blocking running sequence function
def running_sequence():
    global is_stopped
    global starting

    if not is_stopped and starting:  # run this only if the system is not stopped and a new test sequence begins
        if ser and ser.is_open:
            try:
                send_command(ser, 'SHOW RUNNING SEQUENCE')  # send command to request running test updates

                response = ser.readline().decode('utf-8').strip()  # decode serial response

                if response:
                    print(f'about running sequence, arduino says: {response}')
                    listbox.insert(tk.END, response)  # Insert the response into the listbox
                    starting = False  # Reset flag after receiving a response
                else:
                    print('received unexpected message or no valid data')
            except serial.SerialException as e:
                print(f'error reading data: {e}')
                listbox.insert(tk.END, f'error reading data: {e}')

        # Schedule the next call of this function (continue polling for updates)
        window.after(1500, running_sequence)

'''
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
'''

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


#### WRITE TO TXT FILE PART: just the mechanics of it, for future reference ####

# save listbox putput to a text file (for now)
def save_text_file():
    filepath = asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
    )
    if not filepath:
        return
    with open(filepath, mode="w", encoding="utf-8") as output_file:
        text = listbox.get(0, tk.END)
        text_str = "\n".join(text)
        output_file.write(text_str)


###############        GUI PART       ###############

ser = serial_setup()  # necessary start for interactions with arduino

# initialize a new window
window = tk.Tk()
window.title('temperature chamber')
window.configure(bg='white')
# set an initial size for the window (width, height)
window.geometry("680x700")

# prepare the general grid
window.columnconfigure(0, weight=1)  # make sure gui is vertically expandable
window.rowconfigure(0, weight=1)  # and horizontally

# create a canvas to allow scrolling
canvas = tk.Canvas(window, bg='white')
canvas.grid(row=0, column=0, sticky='nsew')  # extend it across the whole window

# add vertical scrollbar
vertical_scrollbar = tk.Scrollbar(window, orient="vertical", command=canvas.yview)
vertical_scrollbar.grid(row=0, column=1, sticky='ns')

# add horizontal scrollbar
horizontal_scrollbar = tk.Scrollbar(window, orient="horizontal", command=canvas.xview)
horizontal_scrollbar.grid(row=1, column=0, sticky='ew')

# configure the canvas to use the scrollbars
canvas.configure(yscrollcommand=vertical_scrollbar.set, xscrollcommand=horizontal_scrollbar.set)

# bind the resizing event of the canvas to update the scrollable region dynamically
def update_scrollregion(event):
    canvas.configure(scrollregion=canvas.bbox("all"))


canvas.bind('<Configure>', update_scrollregion)

# create a frame inside the canvas to hold the rest of the gui
main_frame = tk.Frame(canvas, bg='white')
canvas.create_window((340, 350), window=main_frame, anchor='center')

'''
# define global fonts for specific widgets
window.option_add('*Label.Font', ('Arial', 14, 'bold'))  # Apply to all Label widgets
window.option_add('*Button.Font', ('Arial', 12, 'bold'))  # Apply to all Button widgets
window.option_add('*Entry.Font', ('Arial', 12))          # Apply to all Entry widgets
'''

# TEST FRAME & CONTENT + LOGO + SERIAL MONITOR READOUT BELOW EVERYTHING ELSE
frm_tests = tk.Frame(main_frame, borderwidth=1, highlightthickness=0, bg='white')

# LOGO
image_path = 'C:/Users/owenk/OneDrive/Desktop/Arduino/temperature chamber/temperature_chamber/interface/tkinter/json-driven/arduino_logo.png'  # path to logo file
# use PIL to open the image
logo_image = Image.open(image_path)
logo_image = logo_image.resize((100, 100))  # adjust size
logo_photo = ImageTk.PhotoImage(logo_image)
# create  label for the image
lbl_image = tk.Label(frm_tests, image=logo_photo, bg='white')
lbl_image.image = logo_photo  # keep a reference to avoid garbage collection
lbl_image.grid(row=0, column=0, columnspan=3, sticky='nsew')  # position image

# BENCHMARK TEST PART
lbl_benchmark = tk.Label(frm_tests, text='BENCHMARK TESTS', bg='white')
btn_test1 = tk.Button(frm_tests, text='test 1', bg='white', command=lambda: pick_your_test('test 1'))
btn_test2 = tk.Button(frm_tests, text='test 2', bg='white', command=lambda: pick_your_test('test 2'))
btn_test3 = tk.Button(frm_tests, text='test 3', bg='white', command=lambda: pick_your_test('test 3'))
btn_run_all_benchmark = tk.Button(frm_tests, text='RUN ALL BENCHMARK TESTS', bg='white', command=run_all_benchmark)
btn_save_file = tk.Button(frm_tests, text='save custom test to file', bg="red", command=save_text_file)

# CUSTOM TEST PART
lbl_custom = tk.Label(frm_tests, text='CUSTOM TEST', bg='white')
# buttons to add, remove, and modify steps
btn_add = tk.Button(frm_tests, text='add step', command=add_step, width=30, justify='center', bg='white', fg='black')
btn_remove = tk.Button(frm_tests, text='remove step', command=remove_step, width=30, justify='center', bg='white',
                       fg='black')
btn_modify = tk.Button(frm_tests, text='modify step', command=modify_step, width=30, justify='center', bg='white',
                       fg='black')

# listbox to display the current steps
listbox = Listbox(frm_tests, height=10, width=50)
# temp & duration entries & custom test step handling buttons
ent_temp = tk.Entry(frm_tests, width=30, justify='center', bg='white', fg='black')
ent_duration = tk.Entry(frm_tests, width=30, justify='center', bg='white', fg='black')
btn_add_custom = tk.Button(frm_tests, text='ADD CUSTOM TEST', width=30, justify='center', bg='white', fg='black',
                           command=add_custom)
btn_run_custom = tk.Button(frm_tests, text='RUN CUSTOM TEST', width=30, justify='center', bg='white', fg='black',
                           command=lambda: pick_your_test('custom'))

# run all tests
btn_run_all_tests = tk.Button(frm_tests, text='RUN ALL TESTS', bg='white', command=run_all_tests)

# position labels, buttons and user input widgets in test frame
lbl_benchmark.grid(row=1, column=0, sticky='w', padx=5, pady=5)
btn_save_file.grid(row=2, column=2, rowspan=3, sticky='nsew', padx=5, pady=5)
btn_test1.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
btn_test2.grid(row=3, column=1, sticky='ew', padx=5, pady=5)
btn_test3.grid(row=4, column=1, sticky='ew', padx=5, pady=5)
btn_run_all_benchmark.grid(row=5, column=1, columnspan=2, sticky='ew', padx=5, pady=5)
# custom
lbl_custom.grid(row=6, column=0, sticky='w', padx=5, pady=5)
ent_duration.grid(row=7, column=1, sticky='ew', padx=5, pady=5)
ent_temp.grid(row=7, column=0, sticky='ew', padx=5, pady=5)
btn_add.grid(row=7, column=2, sticky='ew', padx=5, pady=5)
btn_modify.grid(row=8, column=2, sticky='ew', padx=5, pady=5)
btn_remove.grid(row=9, column=2, sticky='ew', padx=5, pady=5)

listbox.grid(row=8, rowspan=5, columnspan=2, sticky='nsew', padx=5, pady=5)

btn_add_custom.grid(row=10, column=2, sticky='ew', padx=5, pady=5)
btn_run_custom.grid(row=11, column=2, sticky='ew', padx=5, pady=5)
btn_run_all_tests.grid(row=16, column=0, columnspan=3, sticky='ew', padx=5, pady=5)

# bind the focus event to the function for both entries
ent_temp.bind('<Button-1>', clear_entry_on_click)
ent_duration.bind('<Button-1>', clear_entry_on_click)
add_placeholder(ent_temp, 'temperature in °C: ')  # ddd placeholder text
add_placeholder(ent_duration, 'duration in minutes: ')

# create & position the STOP button to span across all columns
btn_stop = tk.Button(frm_tests, text='STOP', command=emergency_stop, bg='red', fg='white')
btn_stop.grid(row=19, column=0, columnspan=3, sticky='ew', padx=5, pady=5)

# create and position serial monitor readout lbl
lbl_monitor = tk.Label(frm_tests, text='arduino says things here', bg='#009FAF', fg='white', font='bold')
lbl_monitor.grid(row=20, column=0, columnspan=3, sticky='ew', padx=5, pady=5)


# position both frames
frm_tests.grid(row=0, column=0)

# set data reading from serial every 0.5 second
window.after(500, read_data)
window.after(1000, clear_out_custom)

window.mainloop()