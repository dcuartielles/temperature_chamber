import serial
import time


# create serial communication class
class SerialCommunication:
    def __init__(self, port='COM15', baudrate=9600, timeout=5):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None  # future serial connection object
        self.is_stopped = False  # flag to stop the read loop

    # set up serial communication
    def serial_setup(self, port=None, baudrate=None):
        if port:
            self.port = port  # allow dynamic port change
        if baudrate:
            self.baudrate = baudrate

        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            print(f'connected to arduino port: {self.port}')
            time.sleep(1)  # make sure arduino is ready
            return True
        except serial.SerialException as e:
            print(f'error: {e}')
            return False

    # close serial connection
    def close_serial(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f'connection to {self.port} closed')

    # sends a command to arduino via serial
    def send_command(self, command):
        try:
            if self.ser and self.ser.is_open:
                self.ser.reset_input_buffer()  # clear the gates
                self.ser.write((command + '\n').encode('utf-8'))  # encode command in serial
                print(f'sent command: {command}')  # debug line
                time.sleep(0.02)  # small delay for command processing
            else:
                print('serial connection is not open')

        except serial.SerialException as e:
            print(f'error sending command: {e}')
        except Exception as e:
            print(f'unexpected error: {e}')

    # read data
    def read_data(self):
        if not self.is_stopped and self.ser and self.ser.is_open:
            try:
                self.send_command('SHOW DATA')
                response = self.ser.readline().decode('utf-8').strip()

                if response:
                    print(f'arduino says: {response}')
                    return response
                else:
                    print('there was nothing worth saying here')
                    return None
            except serial.SerialException as e:
                print(f'error reading data: {e}')
                return None
        else:
            print('serial communication is closed or stopped')
            return None

    def capture_all_serial(self, callback=None):
        if not self.is_stopped and self.ser and self.ser.is_open:
            try:
                response = self.ser.readline().decode('utf-8').strip()
                if response:
                    print(response)
                    if callback:
                        callback(response)  # use callback to send data to gui
                else:
                    print('no valid data received')
            except serial.SerialException as e:
                print(f'error reading serial: {e}')

    # emergency stop
    def emergency_stop(self):
        self.is_stopped = True  # set flag to stop the read_data loop
        self.send_command('EMERGENCY STOP')
        print('emergency stop issued')
