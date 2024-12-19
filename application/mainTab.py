from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton,
                             QLineEdit, QHBoxLayout, QMessageBox, QListWidgetItem, QSpacerItem, QApplication)
from PyQt5.QtGui import QColor, QFont
from datetime import datetime
from logger_config import setup_logger

logger = setup_logger(__name__)


class MainTab(QWidget):

    def __init__(self, test_data, parent=None):
        super().__init__(parent)
        self.test_data = test_data
        # test number (index, actually) for checking exp output correctly
        self.test_number = 0
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
        self.instruction_listbox.setFixedSize(540, 135)
        test_part_layout.addLayout(test_output_layout)
        self.run_button = QPushButton('run\ntests', self)
        self.run_button.setFixedSize(96, 96)
        self.run_button.setStyleSheet('background-color: grey;'
                                      'color: white;'
                                      'font-weight: bold;'
                                      'font-size: 20px;'
                                      'border-radius: 48px;'
                                      )
        self.run_button.setEnabled(False)
        test_output_layout.addWidget(self.instruction_listbox)
        test_part_layout.addLayout(test_button_layout)

        # add run tests button
        test_button_layout.addWidget(self.run_button, alignment=Qt.AlignRight)

        # place them in the main layout
        layout.addLayout(test_part_layout)

        # create the alternative test part listboxes for later activation
        self.test_output_label = QLabel('test board output', self)
        self.test_output_label.hide()
        self.test_output_listbox = QListWidget(self)
        self.test_output_listbox.setFixedSize(540, 30)
        self.test_output_listbox.hide()
        test_output_layout.addWidget(self.test_output_label)
        test_output_layout.addWidget(self.test_output_listbox)

        self.expected_outcome_label = QLabel('expected output', self)
        self.expected_outcome_label.hide()
        self.expected_outcome_listbox = QListWidget(self)
        self.expected_outcome_listbox.setFixedSize(540, 30)
        self.expected_outcome_listbox.hide()
        test_output_layout.addWidget(self.expected_outcome_label)
        test_output_layout.addWidget(self.expected_outcome_listbox)

        self.setLayout(layout)

    # TEST RUNNING
    # activate button and set color when serial is running
    def serial_is_running_gui(self):
        self.run_button.setEnabled(True)
        self.run_button.setStyleSheet('background-color: #009FAF;'
                                    'color: white;'
                                    'font-weight: bold;'
                                    'font-size: 20px;'
                                    'border-radius: 48px;')

    # display test board output
    def update_test_output_listbox_gui(self, message):
        self.test_output_listbox.clear()
        self.test_output_listbox.addItem(f'{message}')
        self.test_output_listbox.scrollToBottom()

    # update exp output listbox
    def expected_output_listbox(self):
        expected_output = self.expected_output(self.test_data)
        self.expected_outcome_listbox.clear()
        self.expected_outcome_listbox.addItem(f'{expected_output}')

    # OUTPUT CHECKING PART
    def update_test_number(self, test_number):
        self.test_number = test_number
        logger.info(f'current test number: {self.test_number}')

    # extract expected test outcome from test file
    def expected_output(self, test_data):
        if test_data is not None and 'tests' in test_data:
            all_tests = [key for key in test_data['tests'].keys()]
            current_test_index = self.test_number
            if current_test_index < len(all_tests):
                current_test_key = all_tests[current_test_index]
                test = self.test_data['tests'][current_test_key]
                logger.info(test)
                expected_output = test.get('expected_output', '')  # get pertinent exp output
                logger.info(f'expected output: {expected_output}')
                return expected_output
            else:
                return

    # check if output is as expected
    def check_output(self, message):
        message = str(message) if message else None
        expected_output = self.expected_output(self.test_data)
        # compare t-board output with expected test outcome
        if str(expected_output) == message:
            self.update_gui_correct()
            logger.info("correct test output")
        else:
            logger.error(message)
            # if no matches, handle as incorrect output
            self.update_gui_incorrect()

    # gui for correct output
    def update_gui_correct(self):
        self.test_output_listbox.setStyleSheet("color: #009FAF; font-weight: bold;")
        self.expected_outcome_listbox.setStyleSheet("color: black; font-weight: normal;")

    # gui for incorrect test board output
    def update_gui_incorrect(self):
        self.expected_outcome_listbox.setStyleSheet("color: red; font-weight: bold;")
        self.test_output_listbox.setStyleSheet("color: red; font-weight: bold;")

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

    # simple main tab gui for subsequent sketch uploads between tests
    def sketch_upload_between_tests_gui(self):
        if self.instruction_listbox.isHidden() and self.test_output_listbox.isVisible() and self.expected_outcome_listbox.isVisible() and self.test_output_label.isVisible() and self.expected_outcome_label.isVisible():
            self.test_output_label.hide()
            self.test_output_listbox.hide()
            self.expected_outcome_label.hide()
            self.expected_outcome_listbox.hide()
            self.instruction_listbox.show()
            self.instruction_listbox.clear()
        else:
            self.instruction_listbox.clear()
            QApplication.processEvents()

    # change gui when test interrupted
    def test_interrupted_gui(self):
        if self.instruction_listbox.isHidden() and self.test_output_listbox.isVisible() and self.expected_outcome_listbox.isVisible() and self.test_output_label.isVisible() and self.expected_outcome_label.isVisible():
            self.test_output_label.hide()
            self.test_output_listbox.hide()
            self.expected_outcome_label.hide()
            self.expected_outcome_listbox.hide()
            self.instruction_listbox.show()
            self.instruction_listbox.clear()
            self.instruction_listbox.addItems(['test interrupted, but you can always start over:',
                                               '* upload test file',
                                               '* run full test sequence',
                                               '* sit back and watch the test outcomes'])
            QApplication.processEvents()

        else:
            self.test_output_label.hide()
            self.test_output_listbox.hide()
            self.expected_outcome_label.hide()
            self.expected_outcome_listbox.hide()
            self.instruction_listbox.show()
            self.instruction_listbox.clear()
            self.instruction_listbox.addItems(['* upload test file',
                                           '* run full test sequence',
                                           '* sit back and watch the test outcomes'])
            QApplication.processEvents()

    # test interrupted by manual temperature setting
    def test_interrupted_by_manual_temp_setting_gui(self):
        if self.instruction_listbox.isHidden() and self.test_output_listbox.isVisible() and self.expected_outcome_listbox.isVisible() and self.test_output_label.isVisible() and self.expected_outcome_label.isVisible():
            self.expected_outcome_label.hide()
            self.expected_outcome_listbox.hide()
            self.test_output_label.show()
            self.test_output_listbox.show()
            self.instruction_listbox.show()
            self.instruction_listbox.clear()
            self.instruction_listbox.addItems(['test interrupted, but you can always start over:',
                                               '* you may want to upload test file',
                                               '* run full test sequence',
                                               '* sit back and watch the test outcomes'])
            QApplication.processEvents()

        else:
            self.expected_outcome_label.hide()
            self.expected_outcome_listbox.hide()
            self.test_output_label.show()
            self.test_output_listbox.show()
            self.instruction_listbox.show()
            self.instruction_listbox.clear()
            self.instruction_listbox.addItems(['test interrupted, but you can always start over:',
                                               '* you may want to upload test file',
                                               '* run full test sequence',
                                               '* sit back and watch the test outcomes'])
            QApplication.processEvents()

    # the actual (basic) upper listbox updates
    def cli_update_upper_listbox_gui(self, message):
        self.instruction_listbox.addItem(message)
        self.instruction_listbox.scrollToBottom()
