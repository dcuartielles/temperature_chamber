import json
import logging
from pathlib import Path

from PyQt5.QtWidgets import QFileDialog


# create file handler class
class FileHandler:
    def __init__(self, config, parent=None):
        self.parent = parent  # optional: parent window for the dialog
        self.config = config
        self.test_data = None
        self.filepath = None

    # open a file using a file dialog and return the file content
    def open_file(self):

        if not self.config.config_file.exists():
            self.config.create_default_config()

        initial_dir = self.config.get("test_directory", str(Path.home()))

        # open file dialog to select a JSON file
        filepath, _ = QFileDialog.getOpenFileName(self.parent, "open test file", initial_dir,
                                                  "JSON files (*.json);;"
                                                  "text tiles (*.txt);;"
                                                  "arduino files (*.ino);;"
                                                  "All Files (*)")
        if filepath:
            try:

                with open(filepath, mode='r', encoding='utf-8') as input_file:
                    logging.info(filepath)
                    self.test_data = json.load(input_file)  # convert JSON file content to a py dictionary
                    self.filepath = filepath

                    # update test directory in config to the file's directory
                    test_file_directory = Path(filepath).parent
                    new_test_directory = test_file_directory.parent
                    self.config.set_test_directory(new_test_directory)
                    logging.info(f"test directory updated to: {new_test_directory}")

                    return self.test_data

            except FileNotFoundError:
                print(f'file {filepath} not found.')
                return None

            except json.JSONDecodeError:
                print(f'error decoding JSON from file: {filepath}')
                return None

            except Exception as e:
                print(f'an error occurred: {str(e)}')
                return None

    # return the file path
    def get_filepath(self):
        return self.filepath
