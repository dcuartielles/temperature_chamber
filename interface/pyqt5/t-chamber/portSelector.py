import logging
from PyQt5.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QSpacerItem
import arduinoUtils


# class for the port selection ui
class PortSelector(QWidget):
    def __init__(self, config):
        super().__init__()

        self.config = config  # config object to load/save ports & boards from and to

        self.t_b_name_label = QLabel('test board')
        self.c_b_name_label = QLabel('control board')
        self.t_port_dropdown = QComboBox()
        self.c_port_dropdown = QComboBox()
        self.setStyleSheet('background-color: white;'
                           'color: #009FAF;'
                           'alignment: right;'
                           'font-weight: bold;')

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

        self.load_ports_from_config()

        # connect signals to update config when port & board selection changes
        self.t_port_dropdown.currentIndexChanged.connect(self.update_config_all)
        self.c_port_dropdown.currentIndexChanged.connect(self.update_config_all)

    # load ports and boards from config
    def load_ports_from_config(self):
        saved_t_port = self.config.get('test_board', {}).get('port')
        saved_c_port = self.config.get('control_board', {}).get('port')

        if saved_t_port:
            # find the index in the dropdown corresponding to the saved test board port and set it
            for i in range(self.t_port_dropdown.count()):
                port, _ = self.t_port_dropdown.itemData(i)
                if port == saved_t_port:
                    self.t_port_dropdown.setCurrentIndex(i)
                    break

        if saved_c_port:
            # find the index in the dropdown corresponding to the saved control board port and set it
            for i in range(self.c_port_dropdown.count()):
                port, _ = self.c_port_dropdown.itemData(i)
                if port == saved_c_port:
                    self.c_port_dropdown.setCurrentIndex(i)
                    break

    # refresh ports (independent of config)
    def refresh_ports(self):
        ports_and_boards = arduinoUtils.get_arduino_boards()  # should be [(port, board_name), (port, board_name)]
        self.t_port_dropdown.clear()
        self.c_port_dropdown.clear()
        # add both board name and port to dropdowns
        for port, name in ports_and_boards:
            display_text = f"{name}: {port}"
            self.t_port_dropdown.addItem(display_text)
            self.c_port_dropdown.addItem(display_text)

            # store the port only as item data for easy retrieval
            self.t_port_dropdown.setItemData(self.t_port_dropdown.count() - 1, port)
            self.c_port_dropdown.setItemData(self.c_port_dropdown.count() - 1, port)

    # update config with ports and boards
    def update_config_all(self):
        # get selected ports and board names
        t_port, t_board_name = self.get_selected_t_port_and_board()
        c_port, c_board_name = self.get_selected_c_port_and_board()

        # update the config
        self.config.set_t_board(t_port, t_board_name)
        self.config.set_c_board(c_port, c_board_name)

    # get selected port ONLY for test board / cli worker threads
    def get_selected_t_port(self):
        port, _ = self.t_port_dropdown.itemData(self.t_port_dropdown.currentIndex())
        return str(port)

    # get selected port ONLY for control board worker
    def get_selected_c_port(self):
        port, _ = self.c_port_dropdown.itemData(self.c_port_dropdown.currentIndex())
        return str(port)

    # get both port and board name for test board (for saving in config)
    def get_selected_t_port_and_board(self):
        return self.t_port_dropdown.itemData(self.t_port_dropdown.currentIndex())

    # get both port and board name for control board (for saving in config)
    def get_selected_c_port_and_board(self):
        return self.c_port_dropdown.itemData(self.c_port_dropdown.currentIndex())