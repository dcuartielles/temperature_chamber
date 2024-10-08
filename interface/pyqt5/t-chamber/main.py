# system and PyQt5 imports
import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QLineEdit, QListWidget, QVBoxLayout, QPushButton, QHBoxLayout, QListWidgetItem, QFrame, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt

# functionality imports
from jsonFunctionality import FileHandler

# create window class
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
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
        self.set_temp_input.setPlaceholderText('temperature in °c: ')
        self.set_temp_input.setStyleSheet('color: #009FAF;'
                                          'font-weight: bold')
        self.set_duration_input = QLineEdit(self)
        self.set_duration_input.setPlaceholderText('duration in minutes: ')
        self.set_duration_input.setStyleSheet('color: #009FAF;'
                                              'font-weight: bold')
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
        self.emergency_stop = QPushButton('emergency stop', self)
        self.emergency_stop.setStyleSheet('background-color: red;'
                                          'color: white;'
                                          'font-size: 20px;'
                                          'font-weight: bold;')
        layout.addWidget(self.emergency_stop)

        # connect functionality
        self.load_button.clicked.connect(self.load_test)

        # set layout to the central widget
        self.central_widget.setLayout(layout)
        # automatically adjust window size
        self.adjustSize()

    def load_test(self):
        # create an instance of file handler, pass window as parent
        file_handler = FileHandler(self)
        test_data = file_handler.open_file()


# method responsible for running the app
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

main()