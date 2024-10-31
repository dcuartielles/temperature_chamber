from PyQt5.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QSpacerItem
import arduinoUtils
from PyQt5.QtCore import pyqtSignal
from logger_config import setup_logger

logger = setup_logger(__name__)


# class for the port selection ui
class PortSelector(QWidget):
    ports_refreshed = pyqtSignal()  # signal to re-enable start button

    def __init__(self, config):
        super().__init__()

        self.config = config  # config object to load/save ports & boards from and to

        self.t_b_name_label = QLabel('test board')
        self.c_b_name_label = QLabel('control board')
        self.t_port_dropdown = QComboBox()
        self.c_port_dropdown = QComboBox()
        self.setStyleSheet('background-color: white;'
                           'color: grey;'
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

        # load last used ports if config has a list
        self.load_all_from_config()

        # connect signals to update config when port & board selection changes
        self.t_port_dropdown.currentIndexChanged.connect(self.update_config_t)
        self.c_port_dropdown.currentIndexChanged.connect(self.update_config_c)

        self.update_config_t()
        self.update_config_c()

    # load ports and boards from config
    def load_all_from_config(self):
        saved_t_board = self.config.get('test_board', {})
        saved_c_board = self.config.get('control_board', {})

        # extract ports and board names
        saved_t_port = saved_t_board.get('port')
        saved_t_name = saved_t_board.get('board_name')

        saved_c_port = saved_c_board.get('port')
        saved_c_name = saved_c_board.get('board_name')

        if saved_t_port and saved_t_name:
            for i in range(self.t_port_dropdown.count()):
                display_text = self.t_port_dropdown.itemText(i)
                if display_text == f'{saved_t_name}: {saved_t_port}':
                    self.t_port_dropdown.setCurrentIndex(i)
                    break

        if saved_c_port and saved_c_name:
            for i in range(self.c_port_dropdown.count()):
                display_text = self.c_port_dropdown.itemText(i)
                if display_text == f'{saved_c_name}: {saved_c_port}':
                    self.c_port_dropdown.setCurrentIndex(i)
                    break

    # refresh ports (independent of config)
    def refresh_ports(self):
        self.ports_refreshed.emit()
        logger.info('ports refreshed')
        ports_and_boards = arduinoUtils.get_arduino_boards()  # should be [(port, board_name), (port, board_name)]
        self.t_port_dropdown.clear()
        self.c_port_dropdown.clear()
        # add both board name and port to dropdowns
        for port, name in ports_and_boards:
            display_text = f"{name}: {port}"
            self.t_port_dropdown.addItem(display_text)
            self.c_port_dropdown.addItem(display_text)

    # update config with t port and board
    def update_config_t(self):
        # get selected
        t_port, t_board_name = self.get_selected_t_port_and_board()
        if t_port and t_board_name:
            # update config
            self.config.set_t_board(t_port, t_board_name)

    # update config with c port and board
    def update_config_c(self):
        # get selected
        c_port, c_board_name = self.get_selected_c_port_and_board()
        if c_port and c_board_name:
            # update  config
            self.config.set_c_board(c_port, c_board_name)

    # get selected port ONLY for test board / cli worker threads
    def get_selected_t_port(self):
        saved_t_board = self.config.get('test_board', {})
        saved_t_port = saved_t_board.get('port')
        if saved_t_port:
            return str(saved_t_port)
        else:
            port, _ = self.t_port_dropdown.itemData(self.t_port_dropdown.currentIndex())
            return str(port)

    # get selected port ONLY for control board worker
    def get_selected_c_port(self):
        saved_c_board = self.config.get('control_board', {})
        saved_c_port = saved_c_board.get('port')
        if saved_c_port:
            return str(saved_c_port)
        else:
            port, _ = self.c_port_dropdown.itemData(self.c_port_dropdown.currentIndex())
            return str(port)

    # get both port and board name for test board (for saving in config)
    def get_selected_t_port_and_board(self):
        selected_item = self.t_port_dropdown.currentText()  # get full string
        if selected_item:
            board_name, port = selected_item.split(': ')
            return port, board_name
        return None, None

    # get both port and board name for control board (for saving in config)
    def get_selected_c_port_and_board(self):
        selected_item = self.c_port_dropdown.currentText()
        if selected_item:
            board_name, port = selected_item.split(': ')
            return port, board_name
        return None, None