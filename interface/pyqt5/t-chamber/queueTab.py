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
    set_test_data_and_filepath = pyqtSignal(dict, str)

    def __init__(self, parent=None):

        super().__init__(parent)
        self.test_is_running = False  # flag to know if tests are running
        self.serial_is_running = False  # flag to know if serial is running
        self.test_file_list = {}  # space for list of test file names
        self.test_queue = {}  # space for test queue from arduino
        self.test_data = None
        self.filepath = None
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




'''
{
  “queue”: {
    “queue_length”: 3,
    “test_names”: [
      “Test1",
      “Test2”,
      “Test3"
    ]
  }
  
        self.test_data = self.json_handler.open_file()
        self.filepath = self.json_handler.get_filepath()
'''