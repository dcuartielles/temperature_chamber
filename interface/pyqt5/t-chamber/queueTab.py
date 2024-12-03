from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton,
                             QLineEdit, QHBoxLayout, QMessageBox, QListWidgetItem, QSpacerItem)
from logger_config import setup_logger
import popups

logger = setup_logger(__name__)


class QueueTab(QWidget):

    get_test_file_name = pyqtSignal(str)  # signal from main (from serial) to get directory names for queue updates
    display_queue_from_arduino = pyqtSignal(str)  # signal from main (from serial) to get test names for queue updates
    get_current_test_signal = pyqtSignal(str)  # signal from main (serial) with current running test

    def __init__(self, parent=None):

        super().__init__(parent)
        self.test_is_running = False  # flag to know if tests are running
        self.serial_is_running = False  # flag to know if serial is running
        self.current_test = None
        self.get_test_file_name.connect(self.add_test_name)
        self.display_queue_from_arduino.connect(self.add_arduino_queue)
        self.get_current_test_signal.connect(self.get_current_test_from_signal)
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()  # create a horizontal layout
        layout.setContentsMargins(5, 5, 5, 5)  # add padding around the entire layout

        # add space btw sections: vertical 10px
        layout.addSpacerItem(QSpacerItem(0, 10))

        test_data_layout = QVBoxLayout()  # vertical layout for test data part
        self.test_data_label = QLabel('test upload & names', self)
        self.test_data_list = QListWidget(self)
        self.load_button = QPushButton('upload test', self)
        self.load_button.setStyleSheet('background-color: grey;'
                                        'color: white;')
        self.load_button.setEnabled(False)
        self.clear_queue_button = QPushButton('clear test queue', self)
        self.clear_queue_button.setStyleSheet(('background-color: grey;'
                                        'color: white;'))
        self.clear_queue_button.setEnabled(False)
        test_data_layout.addWidget(self.test_data_label)
        test_data_layout.addWidget(self.test_data_list)
        test_data_layout.addWidget(self.load_button)
        test_data_layout.addWidget(self.clear_queue_button)

        arduino_queue_layout = QVBoxLayout()  # vertical layout for queue display
        self.queue_label = QLabel('test queue', self)
        self.queue_display = QListWidget(self)
        arduino_queue_layout.addWidget(self.queue_label)
        arduino_queue_layout.addWidget(self.queue_display)

        layout.addLayout(test_data_layout)
        layout.addLayout(arduino_queue_layout)

        # add space btw sections: vertical 10px
        layout.addSpacerItem(QSpacerItem(0, 10))

        self.setLayout(layout)

    # set serial is running to true
    def set_serial_is_running_flag_to_true(self):
        self.serial_is_running = True

    # activate buttons and give them colors when serial is running
    def serial_is_running_gui(self):
        self.load_button.setEnabled(True)
        self.clear_queue_button.setEnabled(True)
        self.load_button.setStyleSheet('background-color: #009FAF;'
                                       'color: white;'
                                       'font-weight: bold;'
                                       'font-size: 20px;'
                                       )
        self.clear_queue_button.setStyleSheet('background-color: red;'
                                              'color: white;'
                                              'font-weight: bold;'
                                              'font-size: 20px;'
                                              )

    # serial is not running gui
    def serial_is_not_running_gui(self):
        self.load_button.setEnabled(False)
        self.clear_queue_button.setEnabled(False)
        self.load_button.setStyleSheet('background-color: grey;'
                                       'color: white;'
                                       'font-weight: bold;'
                                       'font-size: 20px;'
                                       )
        self.clear_queue_button.setStyleSheet('background-color: grey;'
                                              'color: white;'
                                              'font-weight: bold;'
                                              'font-size: 20px;'
                                              )

    # add test file name to displayed queue on the left
    def add_test_name(self, names):
        self.test_data_list.clear()  # clear listbox
        name_list = names.split(',')  # split string into test names
        for name in name_list:
            self.test_data_list.addItem(name)

    # add test names to queue on the right
    def add_arduino_queue(self, names):
        self.queue_display.clear()
        name_list = names.split(',')
        for name in name_list:
            self.queue_display.addItem(name)

    # get current test from signal
    def get_current_test_from_signal(self, current_test):
        self.current_test = current_test
        self.highlight_current_test()

    # highlight current test
    def highlight_current_test(self):
        for i in range(self.test_data_list.count()):  # loop through all items in listbox
            item = self.test_data_list.item(i)  # get each item
            if item.text() == self.current_test:
                font = item.font()  # get item's current font
                font.setBold(True)  # change it to bold
                item.setFont(font)  # apply font setting to item
            else:
                font = item.font()
                font.setBold(False)  # reset all others to normal
                item.setFont(font)
