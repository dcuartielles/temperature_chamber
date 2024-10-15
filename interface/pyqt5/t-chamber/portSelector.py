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

        self.t_label = QLabel("test port")
        self.c_label = QLabel("chamber port")
        self.t_port_dropdown = QComboBox()
        self.c_port_dropdown = QComboBox()
        self.setStyleSheet('background-color: white;'
                           'color: #009FAF;'
                           'alignment: right;')

        self.refresh_button = QPushButton("refresh")
        self.refresh_button.clicked.connect(self.refresh_ports)

        layout = QVBoxLayout()
        l_dropdown_layout = QHBoxLayout()
        layout.addLayout(l_dropdown_layout)
        d_dropdown_layout = QHBoxLayout()
        layout.addLayout(d_dropdown_layout)
        l_dropdown_layout.addWidget(self.t_label)
        l_dropdown_layout.addWidget(self.c_label)
        d_dropdown_layout.addWidget(self.t_port_dropdown)
        d_dropdown_layout.addWidget(self.c_port_dropdown)
        layout.addWidget(self.refresh_button)

        self.setLayout(layout)

        # initially populate the dropdown with available ports
        self.refresh_ports()

    def refresh_ports(self):
        ports = get_available_ports()
        self.t_port_dropdown.clear()
        self.t_port_dropdown.addItems(ports)
        self.c_port_dropdown.clear()
        self.c_port_dropdown.addItems(ports)

    def get_selected_port(self):
        return self.t_port_dropdown.currentText() | self.c_port_dropdown.currentText()
