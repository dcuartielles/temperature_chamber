from kivy.app import App
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from functools import partial
import serial
import time
from concurrent.futures import ThreadPoolExecutor
from kivy.clock import Clock

class DropMenu(App):
    def build(self):
        # Set up thread pool executor with 2 workers (one for sending commands, one for reading data)
        self.executor = ThreadPoolExecutor(max_workers=2)

        # Set up serial communication
        try:
            self.ser = serial.Serial("COM15", baudrate=9600, timeout=5)
            print("connected to arduino port: COM15")
        except serial.SerialException as e:
            print(f"error: {e}")
            self.ser = None

        # Main layout
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Create a label to display the Arduino's responses
        self.response_label = Label(text="arduino responses will be displayed here", size_hint=(1, 1))

        # Create a dropdown menu
        dropdown = DropDown()
        commands = [
            "SET TEMP 25",
            "EMERGENCY STOP",
            "SET TEMP "
        ]
        for command in commands:
            btn = Button(text=command, size_hint_y=None, size_hint_x=None, height=44, width=500, background_color=(.8, 0, .9))
            btn.bind(on_release=partial(self.on_dropdown_button_release, command))
            dropdown.add_widget(btn)

        main_button = Button(text='choose what you want to do', size_hint=(None, None), height=44, width=500, background_color=(.8, 0, .9))
        main_button.bind(on_release=dropdown.open)

        dropdown.bind(on_select=self.send_command)

        # Create text input for setting temperature
        self.temperature_input = TextInput(hint_text="degrees?", multiline=False, size_hint=(1, 0.2), background_color=(0, .5, .5), font_size='22sp', halign='center')
        

        # Create text input for setting time
        self.time_input = TextInput(hint_text="minutes on?", multiline=False, size_hint=(1, 0.2), background_color=(0, .5, .5), font_size='22sp', halign='center')

           # Create the "RUN TEST" button
        self.run_test_button = Button(text="RUN TEST", size_hint=(1, 0.2), background_color=(.8, 0, .9))
        self.run_test_button.bind(on_click=self.run_test)
        
        # Add widgets to the main layout
        self.layout.add_widget(main_button)
        self.layout.add_widget(self.response_label)

        # Start a background thread to continuously read from Arduino
        self.executor.submit(self.read_arduino_data)

        return self.layout

    def on_dropdown_button_release(self, command, *args):
        # Handle dropdown button release
        self.send_command(None, command)

        # Show the temperature input box only when "SET TEMP " is chosen
        if command == "SET TEMP ":
            if self.temperature_input not in self.layout.children:
                self.layout.add_widget(self.temperature_input)  # Insert below the label
                self.layout.add_widget(self.time_input)
                self.layout.add_widget(self.run_test_button)
        else:
            # If any other command is selected, remove the temperature input box
            if self.temperature_input in self.layout.children and self.time_input in self.layout.children:
                self.layout.remove_widget(self.temperature_input)
                self.layout.remove_widget(self.time_input)
                self.layout.remove_widget(self.run_test_button)

    def set_temperature(self):
        # Get the user input temperature
        temperature = self.temperature_input.text

        # Check if input is a valid number
        if temperature.replace('.', '', 1).isdigit():
            # Send the "SET TEMP <value>" command to Arduino
            command = f"SET TEMP {temperature}"
            self.send_command(None, command)
        else:
            self.response_label.text = "so that you know, it can only go up to 100°C"
            self.temperature_input.text = ""  # Clear invalid input

    def get_temperature(self):

        if self.ser and self.ser.in_waiting > 0:

            command = "GET TEMP"
            self.send_command(None, command)

            try:
                response = self.ser.readline().decode('utf-8').strip()
                current_temperature = float(response.strip())
                print(f"received: {response}")  # Debug print
                self.response_label.text = f"temperature now: {current_temperature}°C"
                return current_temperature
                
            except Exception as e:
                    self.response_label.text = f"error reading data: {e}"
                    print(f"error reading data: {e}")
        

    def set_time(self):
        # Get the user input time
        time_duration = self.time_input.text

        # Check if input is a valid number
        if time_duration.replace('.', '', 1).isdigit():
            time_in_seconds = int(time_duration) * 60  # Convert minutes to seconds
            current_temperature = self.get_temperature()  # Get current temperature

            if current_temperature and (current_temperature + 0.4 == float(self.temperature_input.text)) and (current_temperature - 0.4 == float(self.temperature_input.text)):
                # Schedule the "SYSTEM OFF" command after the set time
                Clock.schedule_once(partial(self.send_command, None, "SYSTEM OFF"), time_in_seconds)
                self.response_label.text = f"the desired temperature will be held for {time_duration} minutes"
                print(f"the desired temperature will be held for {time_duration} minutes")
            else:
                self.response_label.text = f"temperature now: {current_temperature}°C, still working on it"
        else:
            self.response_label.text = "that won't work"
            self.time_input.text = ""  # Clear invalid input

    def run_test(self, instance):
        self.set_temperature()
        self.set_time()

    def send_command(self, instance, command):
        # Submit the command to be sent in the background
        if self.ser and self.ser.is_open:
            self.executor.submit(self._send_command_task, command)

    def _send_command_task(self, command):
        try:
            self.ser.reset_input_buffer()
            self.ser.write((command + '\n').encode('utf-8'))
            print(f"sent command: {command}")
            self.update_label(f"sent command: {command}")
            time.sleep(1)

        except serial.SerialException as e:
            print(f"Error sending command: {e}")
            self.update_label("error sending command")

    def read_arduino_data(self):
        while self.ser and self.ser.is_open:
            try:
                response = None
                if self.ser.in_waiting > 0:
                    response = self.ser.readline().decode('utf-8').strip()

                if response:  # Only append non-empty responses
                    self.update_label(f"arduino responded: {response}")
                else:
                    self.update_label(f"waiting for arduino response...")

                time.sleep(1)  # Update every second to keep the GUI responsive

            except serial.SerialException as e:
                print(f"error reading data: {e}")
                self.update_label("error reading data")
                break

    def update_label(self, text):
        # Schedule a GUI update from a background thread
        Clock.schedule_once(lambda dt: setattr(self.response_label, 'text', text))

    def on_stop(self):
        # Clean up when the app stops
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Serial port closed.")
        self.executor.shutdown()

if __name__ == '__main__':
    DropMenu().run()