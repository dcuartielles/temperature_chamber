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
    set_test_flag_to_false_signal = pyqtSignal()

    def __init__(self, parent=None):
        self.test_file_list = {}  # space for list of test file names
        self.test_queue = {}  # space for test queue from arduino
        super().__init__(parent)
        self.test_is_running = False  # flag to know if tests are running
        self.serial_is_running = False  # flag to know if serial is running
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()  # create a horizontal layout
        layout.setContentsMargins(5, 5, 5, 5)  # add padding around the entire layout

        # add space btw sections: vertical 10px
        layout.addSpacerItem(QSpacerItem(0, 10))

        test_data_layout = QVBoxLayout()  # vertical layout for test data part
        self.test_data_label = QLabel('test upload & names', self)
        self.test_data_list = QListWidget(self)
        self.upload_button = QPushButton('upload test', self)
        self.clear_queue_button = QPushButton('clear test queue', self)
        test_data_layout.addWidget(self.test_data_label)
        test_data_layout.addWidget(self.test_data_list)
        test_data_layout.addWidget(self.upload_button)
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
'''