from PyQt5.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QSpacerItem
import arduinoUtils


# class for the port selection ui
class PortSelector(QWidget):
    def __init__(self):
        super().__init__()

        self.t_b_name_label = QLabel('board # 1')
        self.c_b_name_label = QLabel('board # 2')
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
        layout.addLayout(port_layout)
        left_layout = QVBoxLayout()
        test_layout = QHBoxLayout()
        chamber_layout = QHBoxLayout()
        test_layout.addWidget(self.t_b_name_label)
        test_layout.addWidget(self.t_port_dropdown)
        chamber_layout.addWidget(self.c_b_name_label)
        chamber_layout.addWidget(self.c_port_dropdown)
        left_layout.addLayout(chamber_layout)
        left_layout.addLayout(test_layout)
        port_layout.addLayout(left_layout)
        port_layout.addSpacerItem(QSpacerItem(30, 0))
        port_layout.addWidget(self.refresh_button)
        port_layout.addSpacerItem(QSpacerItem(30, 0))


        self.setLayout(layout)

        # initially populate the dropdown with available ports
        self.refresh_ports()
    
    def refresh_ports(self):
        ports_and_boards = arduinoUtils.get_arduino_boards()
        self.t_port_dropdown.clear()
        self.t_port_dropdown.addItems(ports_and_boards)
        self.c_port_dropdown.clear()
        self.c_port_dropdown.addItems(ports_and_boards)

    # REFACTOR TO ONLY GET THE PORTS
    def get_selected_t_port(self):
        return self.t_port_dropdown.currentText()

    def get_selected_c_port(self):
        return self.c_port_dropdown.currentText()
