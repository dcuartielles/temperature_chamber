# system and PyQt5 imports
import sys
import logging
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QLineEdit, QListWidget, QVBoxLayout, QPushButton, QHBoxLayout, QListWidgetItem, QFrame, QSpacerItem, QSizePolicy, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QThread, pyqtSignal

# functionality imports
from jsonFunctionality import FileHandler
from serialCaptureWorker import SerialCaptureWorker
from portSelector import PortSelector
from testBoardWorker import TestBoardWorker
from cliWorker import CliWorker


# define global logging
logging.basicConfig(
    filename='serial_data.log',  # log file name
    level=logging.INFO,  # log level
    format='%(asctime)s - %(levelname)s - %(message)s'  # log format
)


# create window class
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # create an instance of json file handler
        self.json_handler = FileHandler(self)

        # create an instance of port selector
        self.port_selector = PortSelector()
        self.selected_c_port = None
        self.selected_t_port = None

        self.serial_worker = None
        self.test_board = None
        self.cli_worker = None

        # create a dictionary for setting temp & duration and space for test file accessible from the worker thread
        self.input_dictionary = []
        self.test_data = None
        self.filepath = None

        self.initUI()

    # method responsible for all gui elements
    def initUI(self):
        # main window and window logo
        self.setWindowTitle('temperature chamber')
        self.setGeometry(600, 110, 0, 0) # decide where on the screen the window will appear
        self.setWindowIcon(QIcon('arduino_logo.png'))
        self.setStyleSheet('background-color: white;'
                           'color: black;')

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

        # port selector
        layout.addWidget(self.port_selector)

        # add space btw sections: vertical 15px
        layout.addSpacerItem(QSpacerItem(0, 15))

        # start button
        self.start_button = QPushButton('start')
        self.start_button.setStyleSheet('background-color: #009FAF;'
                                        'color: white;'
                                        'font-size: 20px;'
                                        'font-weight: bold;')
        layout.addWidget(self.start_button)

        # add space btw sections: vertical 30px
        layout.addSpacerItem(QSpacerItem(0, 30))

        # test handling & layout
        test_part_layout = QHBoxLayout()
        test_button_layout = QVBoxLayout()
        self.instruction_listbox = QListWidget(self)
        self.instruction_listbox.addItems(['* start by choosing ports and boards',
                                           '* upload test file',
                                           '* run full test sequence',
                                           '* sit back and watch the test outcomes'])
        self.instruction_listbox.setFixedSize(475, 135)
        self.load_button = QPushButton('load test file', self)
        self.load_button.setFixedSize(195, 37)
        self.run_button = QPushButton('run benchmark tests', self)
        self.run_button.setFixedSize(195, 37)
        test_part_layout.addWidget(self.instruction_listbox)
        test_part_layout.addLayout(test_button_layout)
        # test selection buttons
        test_button_layout.addWidget(self.load_button, alignment=Qt.AlignRight)
        test_button_layout.addWidget(self.run_button, alignment=Qt.AlignRight)
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

        # place elements
        input_layout.addWidget(self.set_temp_input)
        input_layout.addWidget(self.set_duration_input)

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
        self.chamber_monitor.setStyleSheet('color: #009FAF;')
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

        # add space btw sections: vertical 11px
        layout.addSpacerItem(QSpacerItem(0, 11))

        # connect functionality
        self.start_button.clicked.connect(self.on_start_button_clicked)
        self.load_button.clicked.connect(self.load_test_file)
        self.emergency_stop_button.clicked.connect(self.clear_entries)
        self.run_button.clicked.connect(self.on_run_button_clicked)
        self.set_temp_input.returnPressed.connect(self.on_enter_key)
        self.set_duration_input.returnPressed.connect(self.on_enter_key)

        # set layout to the central widget
        self.central_widget.setLayout(layout)
        # automatically adjust window size
        self.adjustSize()

    # GUI FUNCTIONALITY-RELATED METHODS

    # method to start running threads after ports have been selected
    def on_start_button_clicked(self):
        print('start button clicked')
        # retrieve selected ports after user has had a chance to pick them
        self.selected_c_port = self.port_selector.get_selected_c_port()
        self.selected_t_port = self.port_selector.get_selected_t_port()
        print(self.selected_c_port)  # should return the port string
        print(self.selected_t_port)  # should return the port string

        # only now create the worker threads with the selected ports
        self.serial_worker = SerialCaptureWorker(port=self.selected_c_port, baudrate=9600)
        self.serial_worker.update_listbox.connect(self.update_listbox_gui)
        self.serial_worker.update_chamber_monitor.connect(self.update_chamber_monitor_gui)
        self.serial_worker.start()  # start the worker thread
        self.serial_worker.reset_arduino()
        self.emergency_stop_button.clicked.connect(self.serial_worker.emergency_stop)

        # create test board worker thread
        self.test_board = TestBoardWorker(port=self.selected_t_port, baudrate=9600)
        self.test_board.update_upper_listbox.connect(self.update_upper_listbox_gui)
        self.test_board.start()  # start test board thread


    # the actual chamber_monitor QList updates
    def update_chamber_monitor_gui(self, message):
        self.chamber_monitor.clear()  # clear old data
        item = QListWidgetItem(message)
        item.setTextAlignment(Qt.AlignCenter)
        self.chamber_monitor.addItem(item)

    # the actual listbox updates
    def update_listbox_gui(self, message):
        self.listbox.addItem(message)
        self.listbox.scrollToBottom()

    # the actual upper listbox updates
    def update_upper_listbox_gui(self, message):
        self.instruction_listbox.clear()
        self.instruction_listbox.addItem(message)
        self.instruction_listbox.scrollToBottom()

    def cli_update_upper_listbox_gui(self, message):
        self.instruction_listbox.clear()
        self.instruction_listbox.addItem(message)
        self.instruction_listbox.scrollToBottom()


    # load test file and store it in the app
    def load_test_file(self):
        self.test_data = self.json_handler.open_file()
        self.filepath = self.json_handler.get_filepath()
        if self.test_data:
            print('test data loaded successfully')
        else:
            print('failed to load test data')

    # button click handlers
    #run all benchmark tests
    def on_run_button_clicked(self):
        if self.test_data and self.selected_t_port:  # ensure test data is loaded and t-port is there
            if not self.serial_worker.is_stopped:
                self.serial_worker.run_all_tests(self.test_data)
            if not self.test_board.is_stopped:
                self.test_board.is_running = False
                self.test_board.stop()
                self.test_board.deleteLater()
                logging.info('test board worker temporarily deleted')
                # initiate cli worker thread
                self.cli_worker = CliWorker(port=self.selected_t_port, baudrate=9600)
                # connect pause and resume signals to serial capture
                self.cli_worker.pause_serial.connect(self.serial_worker.pause_capture)
                self.cli_worker.resume_serial.connect(self.serial_worker.resume_capture)
                self.cli_worker.finished.connect(self.cleanup_cli_worker)  # connect finished signal
                self.cli_worker.update_upper_listbox.connect(self.cli_update_upper_listbox_gui)
                self.cli_worker.start()  # start cli worker thread
                self.cli_worker.run_all_tests(filepath=self.filepath, test_data=self.test_data)
                time.sleep(0.1)
        else:
            self.show_error_message('error', 'no test data loaded')

    # clean up cli worker after it's done
    def cleanup_cli_worker(self):

        self.cli_worker.is_running = False
        self.cli_worker.stop()
        logging.info('cli worker quit')
        print('cli worker quit')
        self.cli_worker.deleteLater()
        logging.info('cli worker deleted')
        print('cli worker deleted')

        # time.sleep(2)  # time for the port to fully close before restarting

        # restart test board worker thread
        self.test_board = TestBoardWorker(port=self.selected_t_port, baudrate=9600)
        self.test_board.update_upper_listbox.connect(self.update_upper_listbox_gui)
        self.test_board.start()  # start test board thread
        self.test_board.is_running = True
        print('test board worker restarted')
        logging.info('test board worker restarted')

    # enter for temp & duration inputs
    def on_enter_key(self):
        # check both inputs only when the user presses enter
        temp_string = self.set_temp_input.text().strip()
        duration_string = self.set_duration_input.text().strip()

        if temp_string and duration_string:  # make sure both fields are filled
            is_valid = self.check_inputs(temp_string, duration_string)  # validate inputs

            if is_valid and self.input_dictionary:  # if valid inputs
                self.serial_worker.set_temp(self.input_dictionary)  # set temp in arduino
                print(f'sent to arduino: {self.input_dictionary}')

    # make sure both temp & duration are submitted by user
    def check_inputs(self, temp_string, duration_string):
        is_valid = True  # track overall validity

        try:
            temp = float(temp_string)
            if temp >= 100:
                self.show_error_message('error', 'max temperature = 100°C')
                is_valid = False
        except ValueError:
            self.show_error_message('error', 'numbers only')
            is_valid = False

        try:
            duration = int(duration_string)
            if duration < 1:  # check for minimum duration
                self.show_error_message('error', 'minimum duration is 1 minute')
                is_valid = False
        except ValueError:
            self.show_error_message('error', 'numbers only')  #
            is_valid = False

        if is_valid:
            self.input_dictionary.clear()  # clear previous input
            new_sequence = {'temp': temp, 'duration': duration * 60000}  # convert duration to milliseconds
            self.input_dictionary.append(new_sequence)  # append valid input to the dictionary
            logging.info(self.input_dictionary)  # log temp & duration
        return is_valid

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

    # stop both workers
    def closeEvent(self, event):
        self.serial_worker.stop()
        self.test_board.stop()
        event.accept()  # ensure the application closes


# method responsible for running the app
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

main()