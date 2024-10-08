import json
from PyQt5.QtWidgets import QFileDialog


class FileHandler:
    def __init__(self, parent=None):
        self.parent = parent  # optional: parent window for the dialog

    # open a file using a file dialog and return the file content
    def open_file(self):

        # open file dialog to select a JSON file
        filepath, _ = QFileDialog.getOpenFileName(self.parent, "open test file", "",
                                                  "JSON files (*.json);;"
                                                  "text tiles (*.txt);;"
                                                  "arduino files (*.ino);;"
                                                  "All Files (*)")

        if not filepath:  # if no file was selected
            print("you need to select a file")
            return None

        try:
            with open(filepath, mode='r', encoding='utf-8') as input_file:
                test_data = json.load(input_file)  # convert JSON file content to a py dictionary
                custom = test_data.get('custom', [])  # get the 'custom' list if present

                # adjust 'duration' values if present in the 'custom' steps
                for step in custom:
                    step['duration'] = step['duration'] / 60000  # convert milliseconds to minutes

                return test_data  # return the parsed data

        except FileNotFoundError:
            print(f'File {filepath} not found.')
            return None

######## to be reworked ########


    def send_json_to_arduino(test_data):
        json_data = json.dumps(test_data)  # convert py dictionary to json

        ser.write((json_data + '\n').encode('utf-8'))
        print(f'sent to Arduino: {json_data}')

        # Continuously read Arduino output
        while True:
            if ser.in_waiting > 0:
                response = ser.readline().decode('utf-8').strip()
                print(f'Arduino: {response}')


    # clear out any old custom test from file at the beginning of the session:
    def clear_out_custom():
        test_data = open_file()
        # check if the 'custom' key exists and reset it to an empty list
        if 'custom' in test_data:
            test_data['custom'] = []  # keep the key but clear its contents

        save_file(test_data)  # save the updated dictionary back to the JSON file
        return test_data  # return the Python dictionary

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
                    capture_all_serial()

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
                capture_all_serial()


            elif test_choice == 'test 2':
                test_2 = test_data.get('test_2', [])
                send_json_to_arduino(test_2)
                capture_all_serial()

            elif test_choice == 'test 3':
                test_3 = test_data.get('test_3', [])
                send_json_to_arduino(test_3)
                capture_all_serial()

            else:
                custom_test = test_data.get('custom', [])
                send_json_to_arduino(custom_test)
                capture_all_serial()

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
                    capture_all_serial()
                    # print status and update the listbox
                    print(f'running {test_key}')

                else:
                    print(f'{test_key} not found')
                    listbox.insert(0, f'{test_key} not found or empty')

        else:
            # handle case when no test data is found
            print('no test data found on file')
            listbox.delete(0, tk.END)
            listbox.insert(0, 'no test data found on file')
