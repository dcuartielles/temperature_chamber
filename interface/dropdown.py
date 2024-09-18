from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.base import runTouchApp
import serial
import time

# set up serial communication with arduino
arduino_port = "/dev/cu.usbmodem144301"  # arduino port
baud = 9600
timeout_duration = 5

# list of commands to be on the menu
commands = [
    "SET TEMP 25",
    "EMERGENCY STOP",
    "RESET",
    "REPORT"
]

#make sure there's connection
try:
    ser = serial.Serial(arduino_port, baud, timeout=timeout_duration)
    print("Connected to Arduino port: " + arduino_port)
    time.sleep(2)  # Wait for Arduino to initialize

except serial.SerialException as e:
    print(f"Error: {e}")
    ser = None

#method for sending commands to arduino
def send_command(command):
    if ser and ser.is_open:
        try:
            # Flush the input buffer before writing new data
            ser.reset_input_buffer()

            # Send the selected command to the Arduino
            ser.write((command + '\n').encode('utf-8'))
            print(f"sent command: {command}")

            # Update the label to show that the command was sent
            response_label.text = f"sent command: {command}"

            time.sleep(2)

           # Check for responses from the Arduino
            arduino_responses = []
            while ser.in_waiting > 0:
                response = ser.readline().decode('utf-8').strip()
                if response:
                    arduino_responses.append(response)

            # Update the response label with the Arduino's responses
            if arduino_responses:
                response_label.text = f"arduino responded: {' | '.join(arduino_responses)}"
            else:
                response_label.text = "no response from arduino."
                
            time.sleep(1)

        except serial.SerialException as e:
            print(f"error sending command: {e}")
            response_label.text = f"error sending command: {e}"
    else:
        print("serial connection is not available.")
        response_label.text = "serial connection is not available."

# create a dropdown menu
dropdown = DropDown()

# Create a layout to hold the main button and the response label
layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

# Loop through each command and create a button for it
for command in commands:
    # Create a button for each command
    btn = Button(text=command, size_hint_y=None, size_hint_x=None, height=44, width=500, background_color=(.8, 0, .9))

    # Bind the button press event to send the command when selected
    btn.bind(on_release=lambda btn: dropdown.select(btn.text))

    # Add the button to the dropdown
    dropdown.add_widget(btn)

# Create a main button to show the dropdown
main_button = Button(text='choose what you want to do', size_hint=(None, None), height=44, width=500, background_color=(.8, 0, .9))

# When the main button is pressed, open the dropdown
main_button.bind(on_release=dropdown.open)

# Create a label to display the Arduino's responses
response_label = Label(text="arduino responses will be displayed here.", size_hint=(1, 1))

# Create a callback when a command is selected from the dropdown
dropdown.bind(on_select=lambda instance, x: setattr(main_button, 'text', x) or send_command(response_label))

# Add the main button and response label to the layout
layout.add_widget(main_button)
layout.add_widget(response_label)

# Run the app with the layout
runTouchApp(layout)

# Close the serial connection when done
if ser and ser.is_open:
    ser.close()
    print("Serial port closed.")