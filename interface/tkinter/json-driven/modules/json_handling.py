# imports
import tkinter as tk
from PIL import Image, ImageTk  # for images
import serial
import time
import json
from tkinter import messagebox, Listbox
from tkinter.filedialog import askopenfilename, asksaveasfilename

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
                running_sequence()
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

    if test_data is not None:

        # clear out listbox & entries
        listbox.delete(0, tk.END)
        ent_temp.delete(0, tk.END)
        ent_duration.delete(0, tk.END)

        # handle the test choice
        if test_choice == 'test 1':
            test_1 = test_data.get('test_1', [])
            send_json_to_arduino(test_1)
            running_sequence()
        elif test_choice == 'test 2':
            test_2 = test_data.get('test_2', [])
            send_json_to_arduino(test_2)
            running_sequence()
        elif test_choice == 'test 3':
            test_3 = test_data.get('test_3', [])
            send_json_to_arduino(test_3)
            running_sequence()
        else:
            custom_test = test_data.get('custom', [])
            send_json_to_arduino(custom_test)
            running_sequence()
    else:
        print('no such test on file')
        listbox.insert(0, 'no such test on file')


def run_all_tests():
    test_data = open_file()

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
                running_sequence()
            else:
                print(f'{test_key} not found')
                listbox.insert(0, f'{test_key} not found or empty')

    else:
        # handle case when no test data is found
        print('no test data found on file')
        listbox.delete(0, tk.END)
        listbox.insert(0, 'no test data found on file')
