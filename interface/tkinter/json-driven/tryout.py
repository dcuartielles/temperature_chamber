import tkinter as tk
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
window.mainloop()
