import serial.tools.list_ports
from PyQt5.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget, QPushButton, QHBoxLayout

# helper function to get available serial ports
def get_available_ports():
    ports = serial.tools.list_ports.comports()
    available_ports = [port.device for port in ports]
    return available_ports

# class for the port selection ui
class PortSelector(QWidget):
    def __init__(self):
        super().__init__()

        self.t_b_name_label = QLabel('test board')
        self.c_b_name_label = QLabel('chamber board')
        self.t_port_dropdown = QComboBox()
        self.c_port_dropdown = QComboBox()
        self.setStyleSheet('background-color: white;'
                           'color: #009FAF;'
                           'alignment: right;')

        self.refresh_button = QPushButton('refresh')
        self.refresh_button.setFixedSize(80, 37)
        self.refresh_button.clicked.connect(self.refresh_ports)

        layout = QVBoxLayout()
        port_layout = QHBoxLayout()
        test_layout = QHBoxLayout()
        layout.addLayout(test_layout)
        chamber_layout = QHBoxLayout()
        layout.addLayout(chamber_layout)
        test_layout.addWidget(self.t_b_name_label)
        test_layout.addWidget(self.t_port_dropdown)
        chamber_layout.addWidget(self.c_b_name_label)
        chamber_layout.addWidget(self.c_port_dropdown)
        chamber_layout.addWidget(self.refresh_button)


        self.setLayout(layout)

        # initially populate the dropdown with available ports
        self.refresh_ports()

    def refresh_ports(self):
        ports = get_available_ports()
        self.t_port_dropdown.clear()
        self.t_port_dropdown.addItems(ports)
        self.c_port_dropdown.clear()
        self.c_port_dropdown.addItems(ports)

    def get_selected_t_port(self):
        return self.t_port_dropdown.currentText()

    def get_selected_c_port(self):
        return self.c_port_dropdown.currentText()
