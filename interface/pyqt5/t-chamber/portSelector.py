from PyQt5.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy
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
        self.wifi_t_b_name_label = QLabel('test board wifi port')
        self.wifi_t_b_name_label.hide()
        self.c_b_name_label = QLabel('control board')
        self.t_port_dropdown = QComboBox()
        self.t_wifi_dropdown = QComboBox()
        self.t_wifi_dropdown.hide()
        self.c_port_dropdown = QComboBox()
        self.setStyleSheet('color: #009FAF;'
                                         'background-color: white;'
                                         'alignment: right;'
                                         'font-weight: bold;')

        self.refresh_button = QPushButton('refresh')
        self.refresh_button.setFixedSize(80, 37)
        self.refresh_button.clicked.connect(self.refresh_ports)

        # self.wifi_t_b_name_label.hide()
        # self.t_wifi_dropdown.hide()

        layout = QVBoxLayout()
        port_layout = QHBoxLayout()
        layout.addLayout(port_layout)
        left_layout = QVBoxLayout()
        test_layout = QHBoxLayout()
        chamber_layout = QHBoxLayout()
        wifi_layout = QHBoxLayout()
        wifi_layout.addStretch(1)  # stretch out the space left when this is hidden, for overall layout stability
        test_layout.addWidget(self.t_b_name_label)
        test_layout.addWidget(self.t_port_dropdown)
        chamber_layout.addWidget(self.c_b_name_label)
        chamber_layout.addWidget(self.c_port_dropdown)
        wifi_layout.addWidget(self.wifi_t_b_name_label)
        wifi_layout.addWidget(self.t_wifi_dropdown)
        left_layout.addLayout(chamber_layout)
        left_layout.addLayout(test_layout)
        left_layout.addLayout(wifi_layout)
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
        if self.t_wifi_dropdown.isEnabled:
            self.t_wifi_dropdown.currentIndexChanged.connect(self.update_config_wifi)

        self.update_config_t()  # update test board & port in config
        self.update_config_c()  # update control board & port in config
        if self.t_wifi_dropdown.isEnabled:
            self.update_config_wifi()  # update wifi on t board in config

    # load ports and boards from config
    def load_all_from_config(self):
        # get saved boards from config
        saved_t_board = self.config.get('test_board', {})
        saved_c_board = self.config.get('control_board', {})
        saved_t_b_wifi = self.config.get('t_board_wifi', {})

        # extract ports and board names
        saved_t_port = saved_t_board.get('port')
        saved_t_name = saved_t_board.get('board_name')

        saved_c_port = saved_c_board.get('port')
        saved_c_name = saved_c_board.get('board_name')

        saved_wifi_port = saved_t_b_wifi.get('port')
        saved_wifi_name = saved_t_b_wifi.get('board_name')

        # create a dropdown menu
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

        if saved_wifi_port and saved_wifi_name:
            for i in range(self.t_wifi_dropdown.count()):
                display_text = self.t_wifi_dropdown.itemText(i)
                if display_text == f'{saved_wifi_name}: {saved_wifi_port}':
                    self.t_wifi_dropdown.setCurrentIndex(i)
                    break
        else: return

    # refresh ports (independent of config)
    def refresh_ports(self):
        logger.info('ports refreshed')
        self.ports_refreshed.emit()  # emit signal to re-enable start button click
        ports_and_boards = arduinoUtils.get_arduino_boards()  # should be [(port, board_name), (port, board_name)]
        if not ports_and_boards:
            logger.info('no boards connected')
            return None
        logger.info(ports_and_boards)
        self.t_port_dropdown.clear()
        self.c_port_dropdown.clear()
        self.t_wifi_dropdown.clear()
        # add both board name and port to dropdowns
        if len(ports_and_boards) > 2:
            self.t_wifi_dropdown.show()
            self.t_wifi_dropdown.setDisabled(False)  # enable wifi dropdown
            self.wifi_t_b_name_label.show()
            for port, name in ports_and_boards:
                display_text = f"{name}: {port}"
                self.t_port_dropdown.addItem(display_text)
                self.c_port_dropdown.addItem(display_text)
                self.t_wifi_dropdown.addItem(display_text)
        else:
            self.t_wifi_dropdown.hide()
            # disable wifi dropdown to prevent it from blocking a serial port in the background
            self.t_wifi_dropdown.setDisabled(True)
            self.wifi_t_b_name_label.hide()
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

    # update config with wifi port and board
    def update_config_wifi(self):
        # get selected
        wifi_port, wifi_board_name = self.get_selected_wifi_port_and_board()
        if wifi_port and wifi_board_name:
            # update config
            self.config.set_wifi_board(wifi_port, wifi_board_name)

    # get selected port ONLY (for test board / cli worker thread configuration)
    def get_selected_t_port(self):
        saved_t_board = self.config.get('test_board', {})
        saved_t_port = saved_t_board.get('port')
        if saved_t_port:
            return str(saved_t_port)
        else:
            port, _ = self.t_port_dropdown.itemData(self.t_port_dropdown.currentIndex())
            return str(port)

    # get selected port ONLY for control board worker (for control board / serial worker thread configuration)
    def get_selected_c_port(self):
        saved_c_board = self.config.get('control_board', {})
        saved_c_port = saved_c_board.get('port')
        if saved_c_port:
            return str(saved_c_port)
        else:
            port, _ = self.c_port_dropdown.itemData(self.c_port_dropdown.currentIndex())
            return str(port)

    # get selected port ONLY for wifi
    def get_selected_wifi(self):
        saved_wifi_board = self.config.get('t_board_wifi', {})
        saved_wifi_port = saved_wifi_board.get('port')

        if saved_wifi_port == '':
            if self.t_wifi_dropdown.isEnabled:
                port, _ = self.t_wifi_dropdown.itemData(self.t_wifi_dropdown.currentIndex())
                return str(port)
            else:
                return
        else:
            return str(saved_wifi_port)

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

    # get both port and board name for wifi (for saving in confic)
    def get_selected_wifi_port_and_board(self):
        selected_item = self.t_wifi_dropdown.currentText()
        if selected_item:
            board_name, port = selected_item.split(': ')
            return port, board_name
        return None, None
    