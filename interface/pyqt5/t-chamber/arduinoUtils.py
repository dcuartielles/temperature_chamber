import subprocess

def upload_sketch(board_type, port, sketch_path):

    compile_cmd = ["arduino-cli", "compile", "--fqbn", board_type, sketch_path]
    process_compile = subprocess.run(compile_cmd, capture_output=True, text=True)

    if process_compile.returncode != 0:
        print(f"Compilation failed: {process_compile.stderr}")
        return False

    upload_cmd = ["arduino-cli", "upload", "-p", port, "--fqbn", board_type, sketch_path]
    process_upload = subprocess.run(upload_cmd, capture_output=True, text=True)

    if process_upload.returncode == 0:
        print("Sketch uploaded successfully!")
        return True
    else:
        print(f"Compilation failed: {process_compile.stderr}")
        return False
