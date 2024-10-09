import json
from PyQt5.QtWidgets import QFileDialog
from serialInteraction import SerialCommunication


# create file handler class
class FileHandler:
    def __init__(self, parent=None):
        self.parent = parent  # optional: parent window for the dialog
        # initialize SerialCommunication class to handle serial interactions
        self.serial_com = SerialCommunication()  # create an instance of SC
        self.serial_com.serial_setup(port='COM15', baudrate=9600)

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

    ''' not sure if this is necessary anymore
    # clear out any old custom test from file at the beginning of the session:
    def clear_out_custom(self):
        test_data = self.open_file()
        # check if the 'custom' key exists and reset it to an empty list
        if 'custom' in test_data:
            test_data['custom'] = []  # keep the key but clear its contents

        self.save_file(test_data)  # save the updated dictionary back to the JSON file
        return test_data  # return the python dictionary
    '''

    # send json to arduino
    def send_json_to_arduino(self, test_data):
        json_data = json.dumps(test_data)  # convert py dictionary to json

        if self.serial_com.ser and self.serial_com.ser.is_open:
            self.serial_com.ser.write((json_data + '\n').encode('utf-8'))
            print(f'sent to Arduino: {json_data}')

            # continuously read Arduino output
            while True:
                if self.serial_com.ser.in_waiting > 0:
                    response = self.serial_com.ser.readline().decode('utf-8').strip()
                    print(f'Arduino: {response}')
        else:
            print('serial communication is not open')

    # run the entire test file
    def run_all_tests(self):
        test_data = self.open_file()

        if test_data is not None:
            all_tests = [key for key in test_data.keys()]

            # iterate through each test and run it
            for test_key in all_tests:
                test = test_data.get(test_key, [])

                if test:  # if the test data is available
                    self.send_json_to_arduino(test)  # send the data to Arduino
                    self.serial_com.capture_all_serial(callback=None)
                    # print status and update the listbox
                    print(f'running {test_key}')
                else:
                    print(f'{test_key} not found')

        else:
            # handle case when no test data is found
            print('no test data found on file')

    # run custom only
    def run_custom(self, test_choice):
        test_data = self.open_file()

        if test_data is not None:
            # handle the test choice
            if test_choice == 'custom':
                custom_test = test_data.get('custom', [])
                self.send_json_to_arduino(custom_test)
                self.serial_com.capture_all_serial(callback=None)
        else:
            print('no such test on file')
