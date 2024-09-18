from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.base import runTouchApp

# create a dropdown with 10 buttons
dropdown = DropDown()

commands = [
    "SET TEMP 25",
    "EMERGENCY STOP",
    "RESET",
    "REPORT"
]

# Create a dropdown menu
dropdown = DropDown()

# Loop through each command and create a button for it
for command in commands:
    # Create a button for each command
    btn = Button(text=command, size_hint_y=None, size_hint_x=None, height=44, width=500)

    # Bind the button press event to print the command or perform another action
    btn.bind(on_release=lambda btn: dropdown.select(btn.text))

    # Add the button to the dropdown
    dropdown.add_widget(btn)

# Create a main button to show the dropdown
main_button = Button(text='choose what you want to do', size_hint=(None, None), height=44, width=500)

# When the main button is pressed, open the dropdown
main_button.bind(on_release=dropdown.open)

# Create a callback when a command is selected from the dropdown
dropdown.bind(on_select=lambda instance, x: setattr(main_button, 'text', x))

# Run the app with the main button
runTouchApp(main_button)