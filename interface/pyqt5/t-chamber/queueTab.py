from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton,
                             QLineEdit, QHBoxLayout, QMessageBox, QListWidgetItem, QSpacerItem)
from logger_config import setup_logger
import popups

logger = setup_logger(__name__)


class QueueTab(QWidget):
    add_to_queue_signal = pyqtSignal(dict)  # add tests to queue on control board (set the whole queue as test_data)
    clear_queue_signal = pyqtSignal()  # signal to serial to trigger reset() and interrupt running tests
    show_queue_signal = pyqtSignal(dict)  # signal to serial worker to retrieve test queue from arduino
    clear_queue_from_elsewhere_signal = pyqtSignal()  # signal to clear queue on tests interrupted
    set_test_flag_to_false_signal = pyqtSignal()  # signal to set test_is_running flags to False everywhere
    get_test_file_name = pyqtSignal(str)
    display_queue_from_arduino = pyqtSignal(str)

    def __init__(self, parent=None):

        super().__init__(parent)
        self.test_is_running = False  # flag to know if tests are running
        self.serial_is_running = False  # flag to know if serial is running
        self.test_file_list = {}  # space for list of test file names
        self.test_queue = {}  # space for test queue from arduino
        self.test_data = None
        self.filepath = None
        self.get_test_file_name.connect(self.add_test_name)
        self.display_queue_from_arduino.connect(self.add_arduino_queue)
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

    # get test queue from arduino
    def get_test_queue_from_arduino(self):
        pass

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

    # add test file name to displayed queue on the left
    def add_test_name(self, name):
        self.test_data_list.clear()
        self.test_data_list.addItem(name)
        self.test_data_list.scrollToBottom()

    # add test names to queue on the right
    def add_arduino_queue(self, names):
        self.queue_display.clear()
        self.queue_display.addItem(names)
        self.queue_display.scrollToBottom()

'''
{
    “queue”:
        {“queue_length”:3,
        “tests”:[
            {
                “name”:“test_1”,
                “sketch”:“./alphabet/alphabet.ino”,
                “expected_output”:“ABCDEFGHIJKLMNOPQRSTUVWXYZ”
            },
            {
                “name”:“test_2”,
                “sketch”:“./alphabet_mathematical/alphabet_mathematical.ino”,
                “expected_output”:“ABCDEFGHIJKLMNOPQRSTUVWXYZ120”
            },
            {
                “name”:“test_3”,
                “sketch”:“./alphabet.ino”,
                “expected_output”:“ABCDEFGHIJKLMNOPQRSTUVWXYZ”
            }
        ]
    }
}
  

'''

