import serial.tools.list_ports
from PyQt5.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget, QPushButton

# helper function to get available serial ports
def get_available_ports():
    ports = serial.tools.list_ports.comports()
    available_ports = [port.device for port in ports]
    return available_ports

# class for the port selection ui
class PortSelector(QWidget):
    def __init__(self):
        super().__init__()

        self.label = QLabel("select port:")
        self.port_dropdown = QComboBox()
        self.setStyleSheet('background-color: white;'
                           'color: #009FAF;')

        self.refresh_button = QPushButton("refresh")
        self.refresh_button.clicked.connect(self.refresh_ports)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.port_dropdown)
        layout.addWidget(self.refresh_button)

        self.setLayout(layout)

        # initially populate the dropdown with available ports
        self.refresh_ports()

    def refresh_ports(self):
        ports = get_available_ports()
        self.port_dropdown.clear()
        self.port_dropdown.addItems(ports)

    def get_selected_port(self):
        return self.port_dropdown.currentText()
