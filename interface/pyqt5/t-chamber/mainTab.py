from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton,
                             QLineEdit, QHBoxLayout, QMessageBox, QListWidgetItem, QSpacerItem, QApplication)
from PyQt5.QtGui import QColor, QFont
from datetime import datetime
from logger_config import setup_logger

logger = setup_logger(__name__)


class MainTab(QWidget):

    on_test_interrupted_signal = pyqtSignal()  # signal from main to change gui on test interrupted

    def __init__(self, test_data, parent=None):
        super().__init__(parent)
        self.test_data = test_data
        # connect signal from main
        self.on_test_interrupted_signal.connect(self.on_test_interrupted_gui)
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

    # check if output is as expected
    def check_output(self, message):
        message = str(message) if message else None
        exp_outputs = self.expected_output(self.test_data)

        # compare t-board output with expected test outcome
        for expected in exp_outputs:
            if str(expected) == message:
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

    # the actual (basic) upper listbox updates
    def cli_update_upper_listbox_gui(self, message):
        self.instruction_listbox.addItem(message)
        self.instruction_listbox.scrollToBottom()

    # gui on test interrupted
    def on_test_interrupted_gui(self):
        if self.instruction_listbox.isHidden() and self.test_output_listbox.isVisible() and self.expected_outcome_listbox.isVisible() and self.test_output_label.isVisible() and self.expected_outcome_label.isVisible():
            self.expected_outcome_label.hide()
            self.expected_outcome_listbox.hide()
            self.instruction_listbox.clear()
            self.instruction_listbox.show()
            message = 'no tests are currently running'
            self.cli_update_upper_listbox_gui(message)