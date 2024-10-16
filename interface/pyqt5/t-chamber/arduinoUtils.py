import subprocess
import json
import logging


def run_cli_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.info(f"Command failed: {e}")
        return None


# function to get available arduino boards using arduino-cli
def get_arduino_boards():
    command = ["arduino-cli", "board", "list", "--format", "json"]
    output = run_cli_command(command)

    if output:
        try:
            # parse the output as JSON
            boards_info = json.loads(output)
            arduino_ports = []

            for board in boards_info.get("detected_ports", []):
                if "matching_boards" in board and board["matching_boards"]:
                    port = board.get("port", {}).get("address", "Unknown Port")
                    board_name = board["matching_boards"][0].get("name", "Unknown Board")
                    arduino_ports.append((port, board_name))

            return arduino_ports
        except json.JSONDecodeError:
            logging.info("Error parsing arduino-cli board list output")
            return []
    return []


def detect_board(port):
    command = ["arduino-cli", "board", "list", "--format", "json"]
    output = run_cli_command(command)

    if output:
        boards = json.loads(output)
        for board in boards:
            if board["port"]["address"] == port:
                fqbn = board.get("matching_board", {}).get("fqbn", None)
                if fqbn:
                    logging.info(f"Detected FQBN: {fqbn}")
                    return fqbn
                else:
                    logging.warning(f"No FQBN found for board on port {port}")
                    return None
    return None


def is_core_installed(fqbn):
    core_name = fqbn.split(":")[0]
    command = ["arduino-cli", "core", "list"]
    output = run_cli_command(command)

    if output:
        installed_cores = output.splitlines()
        for core in installed_cores:
            if core_name in core:
                logging.info(f"Core {core_name} is already installed.")
                return True
    return False


def install_core_if_needed(fqbn):
    core_name = fqbn.split(":")[0]
    if not is_core_installed(fqbn):
        logging.info(f"Core {core_name} not installed. Installing...")
        command = ["arduino-cli", "core", "install", core_name]
        run_cli_command(command)
    else:
        logging.info(f"Core {core_name} is already installed.")


def compile_sketch(fqbn, sketch_path):
    logging.info(f"Compiling {sketch_path} for the board with FQBN {fqbn}...")
    command = [
            "arduino-cli", "compile",
            "--fqbn", fqbn,
            sketch_path
            ]
    result = run_cli_command(command)
    if result:
        logging.info(f"Compilation successful!")
        return True
    else:
        logging.warning(f"Compilation failed")
        return False


def upload_sketch(fqbn, port, sketch_path):
    logging.info(f"Uploading {sketch_path} to board with FQBN {fqbn} on port {port}...")
    command = [
            "arduino-cli", "upload",
            "-p", port,
            "--fqbn", fqbn,
            sketch_path
            ]
    result = run_cli_command(command)
    if result:
        logging.info("Upload successful!")
    else:
        logging.warning(f"Upload failed!")


def handle_board_and_upload(port, sketch_path):
    fqbn = detect_board(port)
    if fqbn:
        install_core_if_needed(fqbn)

        if compile_sketch(fqbn, sketch_path):
            upload_sketch(fqbn, port, sketch_path)
        else:
            logging.error(f"Aborting upload due to compilation failure.")
    else:
        logging.warning(f"Failed to detect board on port {port}.")


