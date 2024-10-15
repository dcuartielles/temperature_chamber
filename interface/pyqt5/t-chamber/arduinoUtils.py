import subprocess
import json


def run_cli_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return None


# function to get available arduino boards using arduino-cli
def get_arduino_boards():
    command = ["arduino-cli", "board", "list", "--format", "json"]
    output = run_cli_command(command)

    if output:
        try:
            # parse the output as JSON
            boards = json.loads(output)
            arduino_ports = []

            for board in boards:
                if "boards" in board and board["boards"]:
                    port = board.get("port", "")
                    board_name = board["boards"][0].get("name", "Unknown Board")
                    fqbn = board["boards"][0].get("fqbn", "Unknown FQBN")
                    # add (port, board_name, fqbn) to the list
                    arduino_ports.append((port, board_name, fqbn))

            return arduino_ports
        except json.JSONDecodeError:
            print("Error parsing arduino-cli board list output")
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
                    print(f"Detected FQBN: {fqbn}")
                    return fqbn
                else:
                    print(f"No FQBN found for board on port {port}")
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
                print(f"Core {core_name} is already installed.")
                return True
    return False


def install_core_if_needed(fqbn):
    core_name = fqbn.split(":")[0]
    if not is_core_installed(fqbn):
        print(f"Core {core_name} not installed. Installing...")
        command = ["arduino-cli", "core", "install", core_name]
        run_cli_command(command)
    else:
        print(f"Core {core_name} is already installed.")


def compile_sketch(fqbn, sketch_path):
    print(f"Compiling {sketch_path} for the board with FQBN {fqbn}...")
    command = [
            "arduino-cli", "compile",
            "--fqbn", fqbn,
            sketch_path
            ]
    result = run_cli_command(command)
    if result:
        print(f"Compilation successful!")
        return True
    else:
        print(f"Compilation failed")
        return False


def upload_sketch(fqbn, port, sketch_path):
    print(f"Uploading {sketch_path} to board with FQBN {fqbn} on port {port}...")
    command = [
            "arduino-cli", "upload",
            "-p", port,
            "--fqbn", fqbn,
            sketch_path
            ]
    result = run_cli_command(command)
    if result:
        print("Upload successful!")
    else:
        print(f"Upload failed!")


def handle_board_and_upload(port, sketch_path):
    fqbn = detect_board(port)
    if fqbn:
        install_core_if_needed(fqbn)

        if compile_sketch(fqbn, sketch_path):
            upload_sketch(fqbn, port, sketch_path)
        else:
            print(f"Aborting upload due to compilation failure.")
    else:
        print(f"Failed to detect board on port {port}.")
