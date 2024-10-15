import serial.tools.list_ports


# dynamically choose port
def get_available_ports():
    ports = serial.tools.list_ports.comports()
    available_ports = [port.device for port in ports]
    return available_ports
