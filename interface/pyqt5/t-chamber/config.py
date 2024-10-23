import json
from pathlib import Path

class Config:
    def __init__(self, config_filename='config.json'):
        self.config_file = Path(__file__).parent / config_filename
        self.config = {}
        self.load_config()

    def load_config(self):
        if self.config_file.exists():
            with self.config_file.open('r') as file:
                return json.load(file)
        return {}

    def save_config(self, config_data):
        self.config.update(config_data)
        with self.config_file.open('w') as file:
            json.dump(self.config, file, indent=4)

    def set_c_board(self, port, board_name):
        self.config['control_board'] = {"port": port, "board_name": board_name}
        self.save_config()

    def set_t_board(self, port, board_name):
        self.config['test_board'] = {"port": port, "board_name": board_name}
        self.save_config()

    def set_test_directory(self, directory):
        self.config['test_directory'] = str(Path(directory).resolve())  # store as absolute path
        self.save_config()

    def get_c_port(self):
        return self.config.get('c_port')

    def get_t_port(self):
        return self.config.get('t_port')

    def get_test_directory(self):
        return self.config.get('test_directory')

    def get(self, key, default=None):
        return self.config.get(key, default)