import json
import logging
from pathlib import Path

from PyQt5.QtWidgets import QFileDialog


# create file handler class
class FileHandler:
    def __init__(self, parent=None):
        self.parent = parent  # optional: parent window for the dialog
        self.test_data = None
        self.filepath = None


    # open a file using a file dialog and return the file content
    def open_file(self):

        initial_dir = self.config.get("test_directory", str(Path.home()))

        # open file dialog to select a JSON file
        filepath, _ = QFileDialog.getOpenFileName(self.parent, "open test file", initial_dir,
                                                  "JSON files (*.json);;"
                                                  "text tiles (*.txt);;"
                                                  "arduino files (*.ino);;"
                                                  "All Files (*)")

        if not filepath:  # if no file was selected
            print("you need to select a file")
            return None

        try:

            with open(filepath, mode='r', encoding='utf-8') as input_file:
                logging.info(filepath)
                self.test_data = json.load(input_file)  # convert JSON file content to a py dictionary
                self.filepath = filepath

                return self.test_data

        except FileNotFoundError:
            print(f'file {filepath} not found.')
            return None

    # return the file path
    def get_filepath(self):
        return self.filepath

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

    '''
    # run the entire test file
    def run_all_tests(self):
        test_data = self.test_data

        if test_data is not None:
            all_tests = [key for key in test_data.keys()]

            # iterate through each test and run it
            for test_key in all_tests:
                test = test_data.get(test_key, [])

                if test:  # if the test data is available
                    self.send_json_to_arduino(test)  # send the data to arduino
                    # print status and update the listbox
                    print(f'running {test_key}')
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

    
    # send json to arduino
    def send_json_to_arduino(self, test_data):
        json_data = json.dumps(test_data)  # convert py dictionary to json

        if self.serial_com.ser and self.serial_com.ser.is_open:
            self.serial_com.ser.write((json_data + '\n').encode('utf-8'))
            time.sleep(0.02)
            print(f'sent to arduino: {json_data}')
            # continuously read Arduino output
            while True:
                if self.serial_com.ser.in_waiting > 0:
                    response = self.serial_com.ser.readline().decode('utf-8').strip()
                    # time.sleep(0.02)
                    print(f'arduino says: {response}')
        else:
            print('serial communication is not open') 
    '''