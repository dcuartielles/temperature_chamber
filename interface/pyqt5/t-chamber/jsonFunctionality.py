import json
import time
from PyQt5.QtWidgets import QFileDialog
from serialInteraction import SerialCommunication


# create file handler class
class FileHandler:
    def __init__(self, parent=None):
        self.parent = parent  # optional: parent window for the dialog
        # initialize SerialCommunication class to handle serial interactions
        self.serial_com = SerialCommunication()  # create an instance of SC
        self.serial_com.serial_setup(port='COM15', baudrate=9600)

        self.test_data = None

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
                self.test_data = json.load(input_file)  # convert JSON file content to a py dictionary
                return self.test_data

        except FileNotFoundError:
            print(f'File {filepath} not found.')
            return None

    # save file
    def save_file(self, test_data):
        filepath, _ = QFileDialog.getSaveFileName(self.parent, "save test file", "",
                                                  "JSON files (*.json);;"
                                                  "text tiles (*.txt);;"
                                                  "arduino files (*.ino);;"
                                                  "All Files (*)")

        try:

            # write to a file
            with open(filepath, 'w') as f:
                # convert dictionary to json and write
                json.dump(test_data, f, indent=4)
                print(f'data saved to {filepath}')

        except Exception as e:
            print(f'failed to save file: {e}')

    # send json to arduino
    def send_json_to_arduino(self, test_data):
        json_data = json.dumps(test_data)  # convert py dictionary to json

        if self.serial_com.ser and self.serial_com.ser.is_open:
            try:
                self.serial_com.ser.write((json_data + '\n').encode('utf-8'))
                time.sleep(0.02)
                print(f'sent to arduino: {json_data}')

                # continuously read Arduino output
                if self.serial_com.ser.in_waiting > 0:
                    response = self.serial_com.ser.readline().decode('utf-8').strip()
                    time.sleep(0.02)
                    print(f'arduino says: {response}')
            except Exception as e:
                print(f'got this error: {e}')
        else:
            print('serial communication is not open')

    # run the entire test file
    def run_all_tests(self):
        test_data = self.test_data

        if test_data is not None:
            all_tests = [key for key in test_data.keys()]

            # iterate through each test and run it
            for test_key in all_tests:
                test = test_data.get(test_key, [])

                if test:  # if the test data is available
                    self.send_json_to_arduino(test)  # send the data to Arduino
                    # print status and update the listbox
                    print(f'running {test}')
                else:
                    print(f'{test_key} not found')

        else:
            # handle case when no test data is found
            print('no test data found on file')

    # run custom only
    def run_custom(self):
        test_data = self.test_data

        if test_data is not None:
            custom_test = test_data.get('custom', [])
            if custom_test:
                self.send_json_to_arduino(custom_test)
                print(f'running {custom_test}')
            else:
                print('no custom test found')
        else:
            print('no such test on file')

    # set temp & duration from the gui
    def set_temp(self, input_dictionary):
        if input_dictionary is not None:
            print(input_dictionary)
            self.send_json_to_arduino(input_dictionary)
        else:
            print('nothing to set the t-chamber to')
