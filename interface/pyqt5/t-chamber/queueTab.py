from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton,
                             QLineEdit, QHBoxLayout, QMessageBox, QListWidgetItem, QSpacerItem)
from logger_config import setup_logger
import popups

logger = setup_logger(__name__)


class QueueTab(QWidget):
    # signal to add tests to queue on control board and set the whole queue as test_data
    add_to_queue_signal = pyqtSignal(dict)
    clear_queue_signal = pyqtSignal()  # signal to serial to trigger reset()
    show_queue_signal = pyqtSignal(dict)  # signal to serial worker to retrieve test queue from arduino




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