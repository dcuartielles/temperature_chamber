from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton,
                             QLineEdit, QHBoxLayout, QMessageBox, QListWidgetItem, 
                             QSpacerItem, QApplication, QSizePolicy)
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
        wifi_output_layout = QVBoxLayout()

        self.instruction_listbox = QListWidget(self)
        self.instruction_listbox.addItems(['* start by choosing ports and boards',
                                           '* upload test file',
                                           '* run full test sequence',
                                           '* sit back and watch the test outcomes'])
        self.instruction_listbox.setMinimumSize(300, 100)
        self.instruction_listbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        test_part_layout.addLayout(test_output_layout)
        test_part_layout.addLayout(wifi_output_layout)

        self.run_button = QPushButton('Run\nTests', self)
        self.run_button.setMinimumSize(96, 96)
        self.run_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
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

        # create the alternative test part listboxes for later activation
        self.test_output_label = QLabel('Test Board Output', self)
        self.test_output_label.hide()
        self.test_output_listbox = QListWidget(self)
        self.test_output_listbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.test_output_listbox.setMinimumHeight(30)
        self.test_output_listbox.hide()
        test_output_layout.addWidget(self.test_output_label)
        test_output_layout.addWidget(self.test_output_listbox)

        self.expected_outcome_label = QLabel('Expected Output', self)
        self.expected_outcome_label.hide()
        self.expected_outcome_listbox = QListWidget(self)
        self.expected_outcome_listbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.expected_outcome_listbox.setMinimumHeight(30)
        self.expected_outcome_listbox.hide()
        test_output_layout.addWidget(self.expected_outcome_label)
        test_output_layout.addWidget(self.expected_outcome_listbox)

        # Wifi output section
        self.wifi_output_label = QLabel('Wifi Board Output', self)
        self.wifi_output_label.hide()
        self.wifi_output_listbox = QListWidget(self)
        self.wifi_output_listbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.wifi_output_listbox.setMinimumHeight(30)
        self.wifi_output_listbox.hide()
        wifi_output_layout.addWidget(self.wifi_output_label)
        wifi_output_layout.addWidget(self.wifi_output_listbox)

        self.wifi_expected_label = QLabel('Expected Wifi Output', self)
        self.wifi_expected_label.hide()
        self.wifi_expected_listbox = QListWidget(self)
        self.wifi_expected_listbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.wifi_expected_listbox.setMinimumHeight(30)
        self.wifi_expected_listbox.hide()
        wifi_output_layout.addWidget(self.wifi_expected_label)
        wifi_output_layout.addWidget(self.wifi_expected_listbox)

        # test_part_layout.addLayout(wifi_output_layout)
        # test_output_layout.addWidget(self.wifi_expected_listbox)

        # place them in the main layout
        layout.addLayout(test_part_layout)

        self.setLayout(layout)

    def update_wifi_output_listbox(self, message):
        logger.debug(f'Updating Wifi output listbox with message: {message}')
        self.wifi_output_listbox.clear()
        if message:
            self.wifi_output_listbox.addItem(f'{message}')
            self.wifi_output_listbox.scrollToBottom()
        else:
            logger.warning('Received empty message for Wifi output listbox.')

    def toggle_wifi_output_visibility(self, visible):
        self.wifi_output_label.setVisible(visible)
        self.wifi_output_listbox.setVisible(visible)
        self.wifi_expected_label.setVisible(visible)
        self.wifi_expected_listbox.setVisible(visible)


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

        # Update Wifi expected output if Wifi Worker is running
        wifi_expected_output = self.expected_output(self.test_data)
        self.wifi_expected_listbox.clear()
        self.wifi_expected_listbox.addItem(f'{wifi_expected_output}')

    # OUTPUT CHECKING PART
    def update_test_number(self, test_number):
        self.test_number = test_number
        logger.info(f'Current test number: {self.test_number}')

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
                logger.info(f'Expected output: {expected_output}')
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
            logger.info('Correct test output')
        else:
            logger.error(message)
            # if no matches, handle as incorrect output
            self.update_gui_incorrect()

    # gui for correct output
    def update_gui_correct(self, is_wifi=False):
        if is_wifi:
            self.wifi_output_listbox.setStyleSheet("color: #009FAF; font-weight: bold;")
            self.wifi_expected_listbox.setStyleSheet("color: black; font-weight: normal;")
        else:
            self.test_output_listbox.setStyleSheet("color: #009FAF; font-weight: bold;")
            self.expected_outcome_listbox.setStyleSheet("color: black; font-weight: normal;")

    # gui for incorrect test board output
    def update_gui_incorrect(self, is_wifi=False):
        if is_wifi:
            self.wifi_output_listbox.setStyleSheet("color: red; font-weight: bold;")
            self.wifi_expected_listbox.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.test_output_listbox.setStyleSheet("color: red; font-weight: bold;")
            self.expected_outcome_listbox.setStyleSheet("color: red; font-weight: bold;")

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
