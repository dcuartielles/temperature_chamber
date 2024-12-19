from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QLineEdit, QListWidget, QVBoxLayout, QPushButton, QHBoxLayout, QListWidgetItem, QFrame, QSpacerItem, QSizePolicy, QMessageBox, QTabWidget
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QThread, pyqtSignal


# helper method to display error messages using QMessageBox
def show_error_message(title, message):
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Warning)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec_()  # this will display the message box


# helper method to display info messages using QMessageBox
def show_info_message(title, message):
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Information)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec_()  # this will display the message box


# proceed or not pop-up dialogue window
def show_dialog(message):
    # create a QMessageBox
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Question)
    msg_box.setText(message)
    msg_box.setWindowTitle("are you sure?")
    msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

    # show the dialog and capture the response
    response = msg_box.exec_()

    return response
