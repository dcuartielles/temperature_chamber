import json
from pathlib import Path

class Config:
    def __init__(self, config_file='config.json'):
        self.config_file = Path(config_file).resolve()  # ensure the path is absolute
        self.config = {}
        self.load_config()

    def load_config(self):
        if self.config_file.exists():
            with self.config_file.open('r') as file:
                self.config = json.load(file)
        else:
            # set default values if the config file does not exist
            self.config = {
                "c_port": None,
                "t_port": None,
                "test_directory": None
            }

    def save_config(self):
        with self.config_file.open('w') as file:
            json.dump(self.config, file, indent=4)

    def set_c_port(self, port):
        self.config['c_port'] = port
        self.save_config()

    def set_t_port(self, port):
        self.config['t_port'] = port
        self.save_config()

    def set_test_directory(self, directory):
        self.config['test_directory'] = str(Path(directory).resolve())  # store as absolute path
        self.save_config()

    def get_control_board_port(self):
        return self.config.get('c_port')

    def get_test_board_port(self):
        return self.config.get('t_port')

    def get_test_directory(self):
        return self.config.get('test_directory')
