# system and PyQt5 imports
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QLineEdit, QListWidget, QVBoxLayout, QPushButton, QHBoxLayout, QListWidgetItem, QFrame, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QTimer

# functionality imports
from jsonFunctionality import *
from serialInteraction import *


# create window class
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # create an instance of SerialCommunication
        self.serial_com = SerialCommunication(self)
        self.serial_com.serial_setup(port='COM15', baudrate=9600)

        # create an instance of json file handler
        self.json_handler = FileHandler(self)

        self.initUI()

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
        self.run_button.clicked.connect(self.json_handler.run_all_tests)
        self.custom_button.clicked.connect(self.json_handler.run_custom)

        # set layout to the central widget
        self.central_widget.setLayout(layout)
        # automatically adjust window size
        self.adjustSize()

    '''
    add:
    def clear_entry_on_click(event):
        if event.widget.get() in ['temperature in °C: ', 'numbers only', 'duration in minutes: ', 'max temperature = 100°C',
                                  'enter a number',
                                  'minimum duration is 1 minute']:  # check for placeholder or warning text
            event.widget.delete(0, tk.END)  # clear the entry widget
            event.widget['fg'] = 'black'  # change text color to normal if needed
            
    # CHANGE: SET TEMP & DURATION ONLY
    def add_step():
        test_data = open_file()
    
        if test_data is not None:
            # get input and clear it of potential empty spaces
            temp_string = ent_temp.get().strip()
            duration_string = ent_duration.get().strip()
    
            # initialize temp and duration
            temp = None
            duration = None
            is_valid = True  # track overall validity
    
            if temp_string:
                try:
                    temp = float(temp_string)
                    if temp >= 100:
                        print('max 100')
                        ent_temp.delete(0, tk.END)  # clear the entry
                        ent_temp.insert(0, 'max temperature = 100°C')  # show error message in entry
                        is_valid = False
    
                except ValueError:
                    print('numbers only')
                    ent_temp.delete(0, tk.END)  # clear the entry
                    ent_temp.insert(0, 'numbers only')  # show error message in entry
                    is_valid = False
            else:
                print('no temperature input')
                ent_temp.delete(0, tk.END)  # clear the entry
                ent_temp.insert(0, 'enter a number')  # show error message in entry
                is_valid = False
    
            if duration_string:
                try:
                    duration = int(duration_string)
                    if duration < 1:  # check for a minimum duration 
                        print('minimum duration is 1 minute')
                        ent_duration.delete(0, tk.END)
                        ent_duration.insert(0, 'minimum duration is 1 minute')
                        is_valid = False
                except ValueError:
                    print('numbers only')
                    ent_duration.delete(0, tk.END)  # clear the entry
                    ent_duration.insert(0, 'numbers only')  # show error message in entry
                    is_valid = False
            else:
                print('no valid duration')
                ent_duration.delete(0, tk.END)  # clear the entry
                ent_duration.insert(0, 'enter a number')  # show error message in entry
                is_valid = False
    
                # check if both entries are valid before proceeding
            if is_valid and temp is not None and duration is not None:
                new_sequence = {'temp': temp, 'duration': duration}
                test_data = open_file()
                test_data['custom'].append(new_sequence)
                save_file(test_data)
                update_listbox()
            else:
                print('cannot add custom test due to invalid inputs.')
    
        else:
            print('unable to add custom test due to file loading error')
    '''
    def clear_entries(self):
        self.set_temp_input.clear()
        self.set_duration_input.clear()

    # CHANGE: SET TEMP & DURATION ONLY
    def set_temp(self):
        test_data = self.json_handler.open_file()
        if test_data is not None:
            # get input and clear it of potential empty spaces
            temp_string = self.set_temp_input.get().strip()
            duration_string = self.set_duration_input.get().strip()

            # initialize temp and duration
            temp = None
            duration = None
            is_valid = True  # track overall validity

            if temp_string:
                try:
                    temp = int(temp_string)
                    if temp >= 100:
                        print('max 100')
                        self.set_temp_input.clear()  # clear the entry
                        self.set_temp_input.insert('max temperature = 100°C')  # show error message in entry
                        is_valid = False

                except ValueError:
                    print('numbers only')
                    self.set_temp_input.clear()  # clear the entry
                    self.set_temp_input.insert('numbers only')  # show error message in entry
                    is_valid = False
            else:
                print('no temperature input')
                self.set_temp_input.clear()  # clear the entry
                self.set_temp_input.insert('enter a number')  # show error message in entry
                is_valid = False

            if duration_string:
                try:
                    duration = int(duration_string)
                    if duration < 1:  # check for a minimum duration
                        print('minimum duration is 1 minute')
                        self.set_duration_input.clear()
                        self.set_duration_input.insert('minimum duration is 1 minute')
                        is_valid = False
                except ValueError:
                    print('numbers only')
                    self.set_duration_input.clear()  # clear the entry
                    self.set_duration_input.insert('numbers only')  # show error message in entry
                    is_valid = False
            else:
                print('no valid duration')
                self.set_duration_input.clear()  # clear the entry
                self.set_duration_input.insert('enter a number')  # show error message in entry
                is_valid = False

                # check if both entries are valid before proceeding
            if is_valid and temp is not None and duration is not None:
                new_sequence = {'temp': temp, 'duration': duration}
                test_data = open_file()
                test_data['custom'].append(new_sequence)
                save_file(test_data)
                update_listbox()
            else:
                print('cannot add custom test due to invalid inputs.')

        else:
            print('unable to add custom test due to file loading error')


# method responsible for running the app
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

main()