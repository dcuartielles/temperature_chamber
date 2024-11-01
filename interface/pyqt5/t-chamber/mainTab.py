from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton,
                             QLineEdit, QHBoxLayout, QMessageBox, QListWidgetItem, QSpacerItem, QApplication)
from PyQt5.QtGui import QColor, QFont
from datetime import datetime
from logger_config import setup_logger
import popups

logger = setup_logger(__name__)


class MainTab(QWidget):

    expected_outcome_listbox_signal = pyqtSignal(str)  # signal to show expected test outcome
    incorrect_output = pyqtSignal(str)  # signal to update main

    def __init__(self, test_data, parent=None):
        super().__init__(parent)
        self.test_data = test_data
        self.exp_output = None
        self.expected_outcome_listbox_signal.connect(self.expected_output_listbox_gui)
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
        self.expected_outcome_listbox.setFixedSize(475, 70)
        self.expected_outcome_listbox.hide()
        test_output_layout.addWidget(self.expected_outcome_label)
        test_output_layout.addWidget(self.expected_outcome_listbox)

        self.setLayout(layout)

    # functionality
    # display test board output
    def update_test_output_listbox_gui(self, message):
        self.test_output_listbox.clear()
        self.test_output_listbox.addItem(f'{message}')
        self.test_output_listbox.scrollToBottom()

    # handle correct / incorrect test board output
    def handle_t_board_output(self, status):
        if status:
            self.update_gui_correct()
        else:
            self.update_gui_incorrect()

    # update gui if correct output
    def update_gui_correct(self):
        self.test_output_listbox.setStyleSheet("color: #009FAF; font-weight: bold;")
        self.expected_outcome_listbox.setStyleSheet("color: black; font-weight: normal;")

    # update gui if incorrect output
    def update_gui_incorrect(self):
        self.expected_outcome_listbox.setStyleSheet("color: red; font-weight: bold;")
        self.test_output_listbox.setStyleSheet("color: red; font-weight: bold;")

    # waiting for t-board output
    def reset_gui_for_waiting(self, message):
        self.expected_outcome_listbox.clear()
        self.expected_outcome_listbox.addItem(message)
        logger.info(message)

    # the actual upper listbox updates
    def cli_update_upper_listbox_gui(self, message):
        self.instruction_listbox.addItem(message)
        self.instruction_listbox.scrollToBottom()

    # compare t-board output with expected test outcome
    def check_output(self, readout):
        response = str(readout)
        if self.exp_output == response:
            logger.info("correct test output")
            self.update_gui_correct()
        else:
            date_str = datetime.now().strftime("%m/%d %H:%M:%S")
            error_message = f"{date_str}    incorrect test board output"
            self.incorrect_output.emit(error_message)
            self.update_gui_incorrect()
            logger.error(response)

    # update exp output listbox
    def expected_output_listbox_gui(self, message):
        self.exp_output = str(message)
        logger.info(self.exp_output)
        self.expected_outcome_listbox.addItem(message)
        self.expected_outcome_listbox.scrollToBottom()

    # change test part gui when test is running
    def change_test_part_gui(self, test_data):
        self.test_data = test_data
        self.instruction_listbox.hide()
        self.test_output_label.show()
        self.test_output_listbox.show()
        self.expected_outcome_label.show()
        self.expected_outcome_listbox.show()
        self.expected_output_listbox()

    # change test part gui to show sketch upload progress before test runs
    def on_run_test_gui(self):
        if self.instruction_listbox.isHidden() and self.test_output_listbox.isVisible() and self.expected_outcome_listbox.isVisible() and self.test_output_label.isVisible() and self.expected_outcome_label.isVisible():
            logger.info('update gui on run')
            self.instruction_listbox.show()
            self.instruction_listbox.clear()
            self.test_output_label.hide()
            self.test_output_listbox.hide()
            self.expected_outcome_label.hide()
            self.expected_outcome_listbox.hide()
        else:
            self.instruction_listbox.clear()
            QApplication.processEvents()
