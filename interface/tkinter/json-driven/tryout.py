'''import tkinter as tk
from PIL import Image, ImageTk

# Global variables to track dragging state
dragging_button = None
offset_x = 0
offset_y = 0

def on_round_button_click(test_name):
    print(f"{test_name} round button clicked!")

def create_round_button(parent, x, y, test_name):
    # Create a round button
    button = canvas.create_oval(x - 15, y - 15, x + 15, y + 15, fill="lightblue", outline="blue", width=2)
    # Bind the click event to the button
    canvas.tag_bind(button, "<Button-1>", lambda event: on_round_button_click(test_name))
    # Bind the drag events
    canvas.tag_bind(button, "<ButtonPress-1>", on_drag_start)
    canvas.tag_bind(button, "<B1-Motion>", on_drag_motion)
    canvas.tag_bind(button, "<ButtonRelease-1>", on_drag_release)
    return button

def create_test_buttons():
    # Position of buttons
    y_offset = 60  # Starting y position for the first test button
    y_increment = 40  # Space between buttons

    for i in range(1, 4):  # Assuming you have 3 test buttons
        test_button = tk.Button(frm_tests, text=f"test {i}", bg="white")
        test_button.grid(row=i + 1, column=1, sticky="ew", padx=5, pady=5)

        # Create round button next to the test button
        create_round_button(canvas, 50, y_offset + (i * y_increment), f"Test {i}")

def on_drag_start(event):
    global dragging_button, offset_x, offset_y
    # Store which button is being dragged
    dragging_button = canvas.find_closest(event.x, event.y)[0]
    # Calculate offset to move the button with the mouse
    offset_x = event.x - canvas.coords(dragging_button)[0]
    offset_y = event.y - canvas.coords(dragging_button)[1]

def on_drag_motion(event):
    global dragging_button
    if dragging_button:
        # Move the button with the mouse
        canvas.coords(dragging_button, event.x - offset_x, event.y - offset_y)

def on_drag_release(event):
    global dragging_button
    # Clear the dragging state
    dragging_button = None

# Initialize a new window
window = tk.Tk()
window.title("Temperature Chamber")
window.configure(bg="white")
window.wm_minsize(600, 750)  # Minimum width of 600px and height of 750px

# Create a canvas for drawing round buttons
canvas = tk.Canvas(window, width=600, height=750, bg="white")
canvas.grid(row=0, column=0)

# Create frames
frm_monitor = tk.Frame(window, borderwidth=1, highlightthickness=0, bg="white")
frm_tests = tk.Frame(window, borderwidth=1, highlightthickness=0, bg="white")

# Add the benchmark test buttons and round buttons
create_test_buttons()

# Main loop
window.mainloop()'''


import json
import tkinter as tk
from tkinter import messagebox, Listbox
'''
# Example of loading the JSON file (mock implementation)
def load_file():
    try:
        with open("test_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"custom": []}  # Return an empty structure if file is not found

# Save the updated test data back to the JSON file
def save_file(data):
    with open("test_data.json", "w") as f:
        json.dump(data, f, indent=4)
    print("File saved successfully.")

# Add a step to the custom test
def add_step(temp, duration):
    new_sequence = {"temp": temp, "duration": duration}
    test_data["custom"].append(new_sequence)
    save_file(test_data)
    update_listbox()

# Remove the selected step from the custom test
def remove_step():
    try:
        selected_index = listbox.curselection()[0]  # Get the selected step index
        del test_data["custom"][selected_index]  # Remove the selected step
        save_file(test_data)
        update_listbox()  # Update the listbox display
    except IndexError:
        messagebox.showwarning("Warning", "No step selected to remove!")

# Modify the selected step
def modify_step():
    try:
        selected_index = listbox.curselection()[0]
        temp = float(ent_temp.get().strip())
        duration = int(ent_duration.get().strip())
        test_data["custom"][selected_index] = {"temp": temp, "duration": duration}
        save_file(test_data)
        update_listbox()
    except IndexError:
        messagebox.showwarning("Warning", "No step selected to modify!")
    except ValueError:
        messagebox.showwarning("Warning", "Invalid input!")

# Update the listbox to show the current steps
def update_listbox():
    listbox.delete(0, tk.END)  # Clear current listbox
    for i, step in enumerate(test_data["custom"]):
        listbox.insert(tk.END, f"Step {i + 1}: Temp = {step['temp']}°C, Duration = {step['duration']} mins"'''


#open json file and convert it to py dictionary
def open_file():
    
   #open a file 
    filepath = "C:/Users/owenk/OneDrive/Desktop/Arduino/temperature chamber/temperature_chamber/interface/tkinter/json-driven/test_data.json"

    try:
          with open(filepath, mode="r") as input_file:
                test_data = json.load(input_file)  # convert raw json to py dictionary
                return test_data  # return py dictionary
            
    except FileNotFoundError:
          print(f"file {filepath} not found")
          return None

 # Initial setup

test_data = open_file()

# Save the updated test data back to the JSON file
def save_file(data):
    with open("test_data.json", "w") as f:
        json.dump(data, f, indent=4)
    print("File saved successfully.")

# Add a step to the custom test
def add_step(temp, duration):
    new_sequence = {"temp": temp, "duration": duration}
    test_data["custom"].append(new_sequence)
    save_file(test_data)
    update_listbox()

# Remove the selected step from the custom test
def remove_step():
    try:
        selected_index = listbox.curselection()[0]  # Get the selected step index
        del test_data["custom"][selected_index]  # Remove the selected step
        save_file(test_data)
        update_listbox()  # Update the listbox display
    except IndexError:
        messagebox.showwarning("Warning", "No step selected to remove!")

# Modify the selected step
def modify_step():
    try:
        selected_index = listbox.curselection()[0]
        temp = float(ent_temp.get().strip())
        duration = int(ent_duration.get().strip())
        test_data["custom"][selected_index] = {"temp": temp, "duration": duration}
        save_file(test_data)
        update_listbox()
    except IndexError:
        messagebox.showwarning("Warning", "No step selected to modify!")
    except ValueError:
        messagebox.showwarning("Warning", "Invalid input!")

# Update the listbox to show the current steps
def update_listbox():
    listbox.delete(0, tk.END)  # Clear current listbox
    for i, step in enumerate(test_data["custom"]):
        listbox.insert(tk.END, f"Step {i + 1}: Temp = {step['temp']}°C, Duration = {step['duration']} mins")

# Initial setup
test_data = open_file()

# Tkinter GUI
window = tk.Tk()
window.title("Custom Test Manager")

# Input fields for temp and duration
tk.Label(window, text="Temperature (°C):").pack()
ent_temp = tk.Entry(window)
ent_temp.pack()

tk.Label(window, text="Duration (mins):").pack()
ent_duration = tk.Entry(window)
ent_duration.pack()

# Buttons to add, remove, and modify steps
btn_add = tk.Button(window, text="Add Step", command=lambda: add_step(float(ent_temp.get()), int(ent_duration.get())))
btn_add.pack()

btn_remove = tk.Button(window, text="Remove Step", command=remove_step)
btn_remove.pack()

btn_modify = tk.Button(window, text="Modify Step", command=modify_step)
btn_modify.pack()

# Listbox to display the current steps
listbox = Listbox(window, height=10, width=50)
listbox.pack()

# Populate the listbox with initial data
update_listbox()

# Start the Tkinter main loop
window.mainloop()