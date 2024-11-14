from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton,
                             QLineEdit, QHBoxLayout, QMessageBox, QListWidgetItem, QSpacerItem, QApplication)
from PyQt5.QtGui import QColor, QFont
import re
from datetime import datetime
from logger_config import setup_logger

logger = setup_logger(__name__)


class MainTab(QWidget):

    def __init__(self, test_data, parent=None):
        super().__init__(parent)
        self.test_data = test_data
        self.initUI()

    def initUI(self):

        # create a vertical layout
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)  # add padding around the entire layout

        # test handling & layout
        test_part_layout = QHBoxLayout()
        test_button_layout = QVBoxLayout()
        test_output_layout = QVBoxLayout()
        self.instruction_listbox = QListWidget(self)
        self.instruction_listbox.addItems(['* start by choosing ports and boards',
                                           '* upload test file',
                                           '* run full test sequence',
                                           '* sit back and watch the test outcomes'])
        self.instruction_listbox.setFixedSize(475, 135)
        test_part_layout.addLayout(test_output_layout)

        self.load_button = QPushButton('load test file', self)
        self.load_button.setFixedSize(195, 27)
        self.run_button = QPushButton('run benchmark tests', self)
        self.run_button.setFixedSize(195, 27)
        test_output_layout.addWidget(self.instruction_listbox)
        test_part_layout.addLayout(test_button_layout)

        # test selection buttons
        test_button_layout.addWidget(self.load_button, alignment=Qt.AlignRight)
        test_button_layout.addWidget(self.run_button, alignment=Qt.AlignRight)

        # place them in the main layout
        layout.addLayout(test_part_layout)

        # create the alternative test part listboxes for later activation
        self.test_output_label = QLabel('test board output', self)
        self.test_output_label.hide()
        self.test_output_listbox = QListWidget(self)
        self.test_output_listbox.setFixedSize(475, 30)
        self.test_output_listbox.hide()
        test_output_layout.addWidget(self.test_output_label)
        test_output_layout.addWidget(self.test_output_listbox)

        self.expected_outcome_label = QLabel('expected output', self)
        self.expected_outcome_label.hide()
        self.expected_outcome_listbox = QListWidget(self)
        self.expected_outcome_listbox.setFixedSize(475, 50)
        self.expected_outcome_listbox.hide()
        test_output_layout.addWidget(self.expected_outcome_label)
        test_output_layout.addWidget(self.expected_outcome_listbox)

        self.setLayout(layout)

    # TEST RUNNING
    # display test board output
    def update_test_output_listbox_gui(self, message):
        self.test_output_listbox.clear()
        self.test_output_listbox.addItem(f'{message}')
        self.test_output_listbox.scrollToBottom()

    # update exp output listbox
    def expected_output_listbox(self):
        exp_outputs = self.expected_output(self.test_data)
        self.expected_outcome_listbox.clear()
        for i, output in enumerate(exp_outputs):
            self.expected_outcome_listbox.addItem(f'{output}')
        self.expected_outcome_listbox.scrollToBottom()

    # OUTPUT CHECKING PART
    # extract expected test outcome from test file
    def expected_output(self, test_data):
        if test_data is not None and 'tests' in test_data:
            all_expected_outputs = []
            all_tests = [key for key in test_data['tests'].keys()]
            # iterate through each test and run it
            for test_key in all_tests:
                test = test_data['tests'].get(test_key, {})
                expected_output = test.get('expected output', '')  # get the expected output string
                if expected_output:
                    all_expected_outputs.append(expected_output)
            return all_expected_outputs
        return []

    # encode pattern
    def encode_pattern(self, expected_pattern):
        # escape special characters and use '(.*)' as a placeholder for non-deterministic parts
        regex_pattern = re.escape(expected_pattern).replace(r'\*\*\*', '(.*)')
        regex_pattern = f'^{regex_pattern}$'
        return regex_pattern

    # extract deterministic test output part
    def extract_deterministic_part(self, message, expected_pattern):
        regex_pattern = self.encode_pattern(expected_pattern)
        match = re.match(regex_pattern, message)
        if match:
            # extract non-deterministic captured group '(.*)'
            deterministic_parts = re.split(r'\(\.\*\)', regex_pattern)
            deterministic_output = "".join(deterministic_parts)
            return deterministic_output
        return None

    # check if output is as expected
    def check_output(self, message):
        message = str(message) if message else None
        exp_outputs = self.expected_output(self.test_data)

        # check for missing output
        if message == '':
            self.reset_gui_for_waiting()
            return

        # compare t-board output with expected test output pattern
        match_found = False

        for expected in exp_outputs:
            regex_pattern = self.encode_pattern(expected)
            match = re.match(regex_pattern, message)

            if match:
                # update gui and log
                self.update_gui_correct()
                logger.info("correct test output")

                # log non-deterministic part
                non_deterministic_part = match.group(1) if match.groups() else None
                if non_deterministic_part:
                    logger.info(f"non-deterministic output: {non_deterministic_part}")

                match_found = True
                break  # exit loop as soon as a match is found

        if not match_found:
            # for incorrect outputs, display the full message
            logger.error(f"incorrect output: {message}")
            self.update_gui_incorrect()

    # gui for correct output
    def update_gui_correct(self):
        self.test_output_listbox.setStyleSheet("color: #009FAF; font-weight: bold;")
        self.expected_outcome_listbox.setStyleSheet("color: black; font-weight: normal;")

    # gui for incorrect test board output
    def update_gui_incorrect(self):
        self.expected_outcome_listbox.setStyleSheet("color: red; font-weight: bold;")
        self.test_output_listbox.setStyleSheet("color: red; font-weight: bold;")

    # waiting for t-board output
    def reset_gui_for_waiting(self):
        self.test_output_listbox.clear()
        self.test_output_listbox.addItem("waiting for test board output")
        logger.info("waiting for test board output...")

    # BEFORE TEST IS RUNNING
    # change test part gui to show sketch upload progress before test runs
    def on_run_test_gui(self):
        if self.instruction_listbox.isHidden() and self.test_output_listbox.isVisible() and self.expected_outcome_listbox.isVisible() and self.test_output_label.isVisible() and self.expected_outcome_label.isVisible():
            self.instruction_listbox.show()
            self.instruction_listbox.clear()
            self.instruction_listbox.addItems(['* upload test file',
                                               '* run full test sequence',
                                               '* sit back and watch the test outcomes'])
            self.test_output_label.hide()
            self.test_output_listbox.hide()
            self.expected_outcome_label.hide()
            self.expected_outcome_listbox.hide()
        else:
            self.instruction_listbox.clear()
            QApplication.processEvents()

    # change test part gui when test is running
    def change_test_part_gui(self, test_data):
        self.test_data = test_data
        self.instruction_listbox.hide()
        self.test_output_label.show()
        self.test_output_listbox.show()
        self.expected_outcome_label.show()
        self.expected_outcome_listbox.show()
        self.expected_output_listbox()

    # the actual (basic) upper listbox updates
    def cli_update_upper_listbox_gui(self, message):
        self.instruction_listbox.addItem(message)
        self.instruction_listbox.scrollToBottom()


    '''
    import re
import logging

# Assuming logger is already set up as before

def encode_pattern(expected_pattern):
    """
    Encodes the expected output pattern into a regular expression.
    """
    # Escape special characters and use '(.*)' as a placeholder for non-deterministic parts
    regex_pattern = re.escape(expected_pattern).replace(r'\*\*\*', '(.*)')
    regex_pattern = f'^{regex_pattern}$'
    return regex_pattern

def extract_deterministic_part(message, expected_pattern):
    """
    Extracts and returns the deterministic part of the message based on the expected pattern.
    """
    regex_pattern = encode_pattern(expected_pattern)
    match = re.match(regex_pattern, message)
    
    if match:
        # Deterministic parts are everything except the non-deterministic captured group '(.*)'
        deterministic_parts = re.split(r'\(\.\*\)', regex_pattern)
        deterministic_output = "".join(deterministic_parts)
        return deterministic_output
    return message  # Return the full message if no match is found

def check_output(self, message):
    message = str(message) if message else None
    exp_outputs = self.expected_output(self.test_data)

    # Check for missing output
    if message == '':
        self.reset_gui_for_waiting()
        return

    # Compare test board output with each expected pattern
    match_found = False
    displayed_output = None  # To store the deterministic part for display

    for expected in exp_outputs:
        regex_pattern = encode_pattern(expected)
        match = re.match(regex_pattern, message)
        
        if match:
            # Extract and store the deterministic part
            displayed_output = extract_deterministic_part(message, expected)
            
            # Update GUI and log the output
            self.update_gui_correct()
            logger.info("Correct test output")

            # Log the full message (including non-deterministic part) if necessary
            non_deterministic_part = match.group(1) if match.groups() else None
            if non_deterministic_part:
                logger.info(f"Non-deterministic output: {non_deterministic_part}")
            
            match_found = True
            break  # Exit loop as soon as a match is found

    if not match_found:
        # If no matches, handle as incorrect output
        displayed_output = message  # For incorrect outputs, display the full message
        logger.error(f"Incorrect output: {message}")
        self.update_gui_incorrect()

    # Display only the deterministic part of the output
    self.display_output(displayed_output)

def display_output(self, output):
    """
    Displays the output in the GUI.
    """
    # Replace this with your GUI logic to display the output
    print(f"Displayed Output: {output}")

    '''