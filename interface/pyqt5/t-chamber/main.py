# system and PyQt5 imports
import sys
import threading
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QLineEdit, QListWidget, QVBoxLayout, QPushButton, QHBoxLayout, QListWidgetItem, QFrame, QSpacerItem, QSizePolicy, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QThread, pyqtSignal

# functionality imports
from jsonFunctionality import FileHandler
from serialInteraction import SerialCommunication
from chamberMonitorWorker import ChamberMonitorWorker
from serialCaptureWorker import SerialCaptureWorker


# create window class
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # create an instance of SerialCommunication
        self.serial_com = SerialCommunication(self)
        self.serial_com.serial_setup(port='COM15', baudrate=9600)

        # create an instance of json file handler
        self.json_handler = FileHandler(self)

        # create a dictionary for setting temp & duration
        self.input_dictionary = {}

        self.initUI()

        # create chamber monitor worker thread
        self.chamber_worker = ChamberMonitorWorker(self.serial_com)
        self.chamber_worker.update_chamber_monitor.connect(self.update_chamber_monitor)

        # create serial capture worker thread
        self.capture_worker = SerialCaptureWorker(self.serial_com)
        self.capture_worker.update_instruction_listbox.connect(self.update_instruction_listbox)

        # start the chamber monitor worker
        self.chamber_worker.start()

    # method responsible for all gui elements
    def initUI(self):
        # main window and window logo
        self.setWindowTitle('temperature chamber')
        self.setGeometry(600, 200, 0, 0) # decide where on the screen the window will appear
        self.setWindowIcon(QIcon('arduino_logo.png'))
        self.setStyleSheet('background-color: white;')

        # central widget to hold layout
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # create a vertical layout
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)  # add padding around the entire layout

        # logo
        self.im_label = QLabel(self)
        pixmap = QPixmap('arduino_logo.png')
        self.im_label.setPixmap(pixmap)
        self.im_label.setScaledContents(True)
        self.im_label.setFixedSize(100, 100)  # define logo dimensions
        layout.addWidget(self.im_label, alignment=Qt.AlignLeft)  # add logo to the layout

        # test handling & layout
        test_part_layout = QHBoxLayout()
        test_button_layout = QVBoxLayout()
        self.instruction_listbox = QListWidget(self)
        self.instruction_listbox.addItems(['* start by loading a test from a file',
                                           '* make sure the serial port number is correct',
                                           '* run full test sequence',
                                           '* or run just custom test'])
        self.instruction_listbox.setFixedSize(475, 135)
        self.load_button = QPushButton('load test', self)
        self.load_button.setFixedSize(195, 37)
        self.run_button = QPushButton('run test', self)
        self.run_button.setFixedSize(195, 37)
        self.custom_button = QPushButton('run custom test only', self)
        self.custom_button.setFixedSize(195, 37)
        test_part_layout.addWidget(self.instruction_listbox)
        test_part_layout.addLayout(test_button_layout)
        test_button_layout.addWidget(self.load_button, alignment=Qt.AlignRight)
        test_button_layout.addWidget(self.run_button, alignment=Qt.AlignRight)
        test_button_layout.addWidget(self.custom_button, alignment=Qt.AlignRight)
        # place them in the main layout
        layout.addLayout(test_part_layout)

        # add space btw sections: vertical 20px
        layout.addSpacerItem(QSpacerItem(0, 20))

        # set temperature and duration in their own layout part
        input_layout = QHBoxLayout()
        self.set_temp_input = QLineEdit(self)
        self.set_temp_input.setPlaceholderText('temperature in °C :')
        self.set_temp_input.setStyleSheet('color: #009FAF;')
        self.set_duration_input = QLineEdit(self)
        self.set_duration_input.setPlaceholderText('duration in minutes: ')
        self.set_duration_input.setStyleSheet('color: #009FAF;')
        self.set_button = QPushButton('set', self)
        input_layout.addWidget(self.set_temp_input)
        input_layout.addWidget(self.set_duration_input)
        input_layout.addWidget(self.set_button)
        # add input layout part to main layout
        layout.addLayout(input_layout)

        # add space btw sections: vertical 20px
        layout.addSpacerItem(QSpacerItem(0, 20))

        # listbox for test updates
        self.serial_label = QLabel('running test info', self)
        self.listbox = QListWidget(self)
        layout.addWidget(self.serial_label)
        layout.addWidget(self.listbox)

        # add space btw sections: vertical 20px
        layout.addSpacerItem(QSpacerItem(0, 20))

        # listbox for temperature chamber monitoring
        self.chamber_label = QLabel('temperature chamber situation', self)
        self.chamber_monitor = QListWidget(self)
        self.chamber_monitor.setFixedHeight(40)
        self.chamber_monitor.setStyleSheet('color: #009FAF;'
                                           'font-size: 20px;')
        # create a QListWidgetItem with centered text
        item = QListWidgetItem('arduino will keep you posted on current temperature and such')
        item.setTextAlignment(Qt.AlignCenter)  # center text
        self.chamber_monitor.addItem(item)
        layout.addWidget(self.chamber_label)
        layout.addWidget(self.chamber_monitor)

        # add space btw sections: vertical 20px
        layout.addSpacerItem(QSpacerItem(0, 20))

        # emergency stop button
        self.emergency_stop_button = QPushButton('emergency stop', self)
        self.emergency_stop_button.setStyleSheet('background-color: red;'
                                                 'color: white;'
                                                 'font-size: 20px;'
                                                 'font-weight: bold;')
        layout.addWidget(self.emergency_stop_button)

        # connect functionality
        self.load_button.clicked.connect(self.json_handler.open_file)
        self.emergency_stop_button.clicked.connect(self.serial_com.emergency_stop)
        self.emergency_stop_button.clicked.connect(self.clear_entries)
        self.run_button.clicked.connect(self.on_run_button_clicked)
        self.custom_button.clicked.connect(self.on_custom_button_clicked)
        self.set_button.clicked.connect(self.set_temp_and_duration)

        # set layout to the central widget
        self.central_widget.setLayout(layout)
        # automatically adjust window size
        self.adjustSize()

    # GUI FUNCTIONALITY-RELATED METHODS
    # the actual chamber_monitor QList updates
    def update_chamber_monitor(self, message):
        self.chamber_monitor.clear()  # clear old data
        item = QListWidgetItem(message)
        item.setTextAlignment(Qt.AlignCenter)
        self.chamber_monitor.addItem(item)

    # the actual instruction listbox updates
    def update_instruction_listbox(self, message):
        self.instruction_listbox.addItem(message)
        self.instruction_listbox.scrollToBottom()

    # button click handlers
    def on_run_button_clicked(self):
        if not self.capture_worker.isRunning():
            self.capture_worker.start()
        self.instruction_listbox.clear()  # clear the listbox initially if needed
        # run tests
        self.json_handler.run_all_tests()

    def on_custom_button_clicked(self):
        if not self.capture_worker.isRunning():
            self.capture_worker.start()
        self.instruction_listbox.clear()  # clear the listbox initially if needed
        # run custom test
        self.json_handler.run_custom('custom')

    # stop both workers
    def closeEvent(self, event):
        self.chamber_worker.stop()
        self.capture_worker.stop()
        super().closeEvent(event)

    # set tem & duration independently of test file
    def set_temp_and_duration(self):
        # get input and clear it of potential empty spaces
        temp_string = self.set_temp_input.text().strip()
        duration_string = self.set_duration_input.text().strip()

        # initialize temp and duration
        temp = None
        duration = None
        is_valid = True  # track overall validity

        if temp_string:
            try:
                temp = int(temp_string)
                if temp >= 100:
                    print('max 100')
                    self.show_error_message('error', 'max temperature = 100°C')  # show error message
                    is_valid = False

            except ValueError:
                print('numbers only')
                self.show_error_message('error', 'numbers only')  # show error message
                is_valid = False
        else:
            print('no temperature input')
            self.show_error_message('error', 'enter a number')  # show error message
            is_valid = False

        if duration_string:
            try:
                duration = int(duration_string)
                if duration < 1:  # check for a minimum duration
                    print('minimum duration is 1 minute')
                    self.show_error_message('error', 'minimum duration is 1 minute')
                    is_valid = False
            except ValueError:
                print('numbers only')
                self.show_error_message('error', 'numbers only')
                is_valid = False
        else:
            print('no valid duration')
            self.show_error_message('error', 'enter a number')  # show error message in entry
            is_valid = False

        # check if both entries are valid before proceeding
        if is_valid and temp is not None and duration is not None:
            self.input_dictionary = {'temp': temp, 'duration': duration}
            self.json_handler.set_temp(self.input_dictionary)
            print('temp and duration set')
        else:
            print('invalid inputs')

    # helper method to display error messages using QMessageBox
    @staticmethod  # makes it smoother in use, as it doesn't require access to any instance-specific data
    def show_error_message(title, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()  # this will display the message box

    # auxiliary method for emergency stop
    def clear_entries(self):
        self.set_temp_input.clear()
        self.set_duration_input.clear()

# method responsible for running the app
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

main()