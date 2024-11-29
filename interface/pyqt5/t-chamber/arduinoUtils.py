import subprocess
import json
from logger_config import setup_logger

logger = setup_logger(__name__)


def run_cli_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.info(f"Command failed: {e}")
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

            # hypothetical handling for network-based boards
            for network_board in boards_info.get("network_ports", []):
                if "matching_boards" in network_board and network_board["matching_boards"]:
                    port = network_board.get("port", {}).get("address", "Unknown Network Port")
                    board_name = network_board["matching_boards"][0].get("name", "Unknown Board")
                    arduino_ports.append((port, board_name))

            logger.info(f'arduino_ports: {arduino_ports}')
            return arduino_ports
        except json.JSONDecodeError:
            logger.info("error parsing arduino-cli board list output")
            return []
    return []


def detect_board(port):
    command = ["arduino-cli", "board", "list", "--format", "json"]
    output = run_cli_command(command)

    if output:
        boards_info = json.loads(output)
        for board in boards_info.get("detected_ports", []):
            if board["port"]["address"] == port:
                if "matching_boards" in board and board["matching_boards"]:
                    fqbn = board["matching_boards"][0].get("fqbn", None)
                    if fqbn:
                        logger.info(f"Detected FQBN: {fqbn}")
                        return fqbn
                    else:
                        logger.warning(f"No FQBN found for board on port {port}")
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
                logger.info(f"Core {core_name} is already installed.")
                return True
    return False


def install_core_if_needed(fqbn):
    core_name = fqbn.split(":")[0]
    if not is_core_installed(fqbn):
        logger.info(f"Core {core_name} not installed. Installing...")
        command = ["arduino-cli", "core", "install", core_name]
        run_cli_command(command)
    else:
        logger.info(f"Core {core_name} is already installed.")


def compile_sketch(fqbn, sketch_path):
    logger.info(f"Compiling {sketch_path} for the board with FQBN {fqbn}...")
    command = [
            "arduino-cli", "compile",
            "--fqbn", fqbn,
            sketch_path
            ]
    result = run_cli_command(command)
    if result:
        logger.info(f"Compilation successful!")
        return True
    else:
        logger.warning(f"Compilation failed")
        return False


def upload_sketch(fqbn, port, sketch_path):
    logger.info(f"Uploading {sketch_path} to board with FQBN {fqbn} on port {port}...")
    command = [
            "arduino-cli", "upload",
            "-p", port,
            "--fqbn", fqbn,
            sketch_path
            ]
    result = run_cli_command(command)
    if result:
        logger.info("Upload successful!")
    else:
        logger.warning(f"Upload failed!")


def handle_board_and_upload(port, sketch_path):
    fqbn = detect_board(port)
    if fqbn:
        install_core_if_needed(fqbn)

        if compile_sketch(fqbn, sketch_path):
            upload_sketch(fqbn, port, sketch_path)
        else:
            logger.error(f"Aborting upload due to compilation failure.")
    else:
        logger.warning(f"Failed to detect board on port {port}.")

