#imports
import tkinter as tk
from PIL import Image, ImageTk #for images
import serial
import time
import json
#in case you want to use file finder
from tkinter.filedialog import askopenfilename, asksaveasfilename 


# global flag for stopping the reading process
is_stopped = False


###############        FUNCTIONALITY AND LOGIC       ###############

#### JSON HANDLING ####

#send json through serial / run all tests
def send_json_to_arduino(test_data):
        
        json_data = json.dumps(test_data) #convert py dictionary to json
        
        ser.write((json_data + '\n').encode('utf-8'))
        print(f"Sent to Arduino: {json_data}")

        # Continuously read Arduino output
        while True:
            if ser.in_waiting > 0:
                response = ser.readline().decode('utf-8').strip()
                print(f"Arduino: {response}")
            time.sleep(1)


#open json file and convert it to py dictionary
def open_file():
    
   #open a file 
    filepath = "C:/Users/owenk/OneDrive/Desktop/Arduino/temperature chamber/temperature_chamber/interface/tkinter/test_data.json"

    try:
          with open(filepath, mode="r") as input_file:
                test_data = json.load(input_file)  # convert raw json to py dictionary
                return test_data  # return py dictionary
            
    except FileNotFoundError:
          print(f"file {filepath} not found")
          return None
    
#save input dictionary to json file
def save_file(test_data):
    
    filepath = "C:/Users/owenk/OneDrive/Desktop/Arduino/temperature chamber/temperature_chamber/interface/tkinter/test_data.json"

    try:
    
          # Write to a file
          with open(filepath, 'w') as f:
              #convert dictionary to json and write
              json.dump(test_data, f, indent=4)
              print(f"data seved to {filepath}")

    except Exception as e:
         print(f"failed to save file: {e}")


#add custom test
def add_custom(temp, duration):
    
    test_data = open_file()

    if test_data is not None:
        # add new sequence to the list
        new_sequence = {"temp": temp, "duration": duration}
        test_data["custom"].append(new_sequence)  # append new custom test
        save_file(test_data)  # save back to JSON file

    else:
        print("unable to add custom test due to file loading error")

'''
#pick your test method0p
def pick_your_test():
     
    test_data = open_file()
    test_choice = user_input.get("text")

    if test_data is not None:
          if test_choice = "test 1":
              test_1 = test_data.get("test_1", [])
              send_json_to_arduino(test_1)
          elif test_choice =  "test 2":
              test_2 = test_data.get("test_2", [])
              send_json_to_arduino(test_2)
          elif test_choice = "test 3":
              test_3 = test_data.get("test_3", [])
              send_json_to_arduino(test_3)
          else:
              custom_test = test_data.get("custom", [])8z
              send_json_to_arduino(custom_test)
     
           

def open_custom_tests():
    filepath = "C:/Users/owenk/OneDrive/Desktop/Arduino/temperature chamber/temperature_chamber/interface/tkinter/test_data.json"
    
    try:
        with open(filepath, mode="r") as input_file:
            test_data = json.load(input_file)  # Load the JSON content as a dictionary
            
            # Extract only the custom tests if they exist
            custom_tests = test_data.get("custom", [])
            return custom_tests
    except FileNotFoundError:
        print(f"File {filepath} not found.")
        return None'''


#### SERIAL INTERACTION ####

# emergency stop
def emergency_stop():
    global is_stopped
    is_stopped = True #set flag to stop the read_data loop

    command = "EMERGENCY STOP"
    send_command(ser, command)
    lbl_monitor["text"] = "EMERGENCY STOP"


#parse decoded serial response for smooth data extraction
def parse_serial_response(response):
    # split the response string into key-value pairs
    data = response.split(" | ")

    # create a dictionary to store parsed values
    parsed_data = {}

    # loop through each key-value pair and split by ":"
    for item in data:
        key, value = item.split(": ")
        
        # clean the key and value, and store them in the dictionary
        key = key.strip()
        value = value.strip()
        
        # assign specific values based on key
        if key == "Room_temp":
            parsed_data["Room_temp"] = float(value)
        elif key == "Desired_temp":
            parsed_data["Desired_temp"] = float(value)
        elif key == "Heater":
            parsed_data["Heater"] = bool(int(value))  # convert '1' or '0' to True/False
        elif key == "Cooler":
            parsed_data["Cooler"] = bool(int(value))  # convert '1' or '0' to True/False

    return parsed_data


#read data from serial
def read_data():
    
    global is_stopped

    if not is_stopped:  # only read data if the system is not stopped
        if ser and ser.is_open:
            try:
                send_command(ser, "SHOW DATA")  # send command to request data
                time.sleep(0.2)  # wait for arduino to process the command

                response = ser.readline().decode('utf-8').strip() #decode serial response

                # parse the response
                parsed_data = parse_serial_response(response)
                room_temp = parsed_data.get("Room_temp", None)
                desired_temp = parsed_data.get("Desired_temp", None)
                heater_status = parsed_data.get("Heater", None)
                cooler_status = parsed_data.get("Cooler", None)

                if response:
                    print(f"arduino responded: {response}")
                    lbl_monitor["text"] = f"{response}"
                    lbl_r_temp["text"] = f"{room_temp}°C"
                    lbl_d_temp["text"] = f"{desired_temp}°C"
                    lbl_heater_status["text"] = f"{'ON' if heater_status else 'OFF'}"
                    lbl_cooler_status["text"] = f"{'ON' if cooler_status else 'OFF'}"
                else:
                    print("received unexpected message or no valid data.")
                    lbl_monitor["text"] = "received unexpected message or no valid data."

            except serial.SerialException as e:
                print(f"Error reading data: {e}")
                lbl_monitor["text"] = f"Error reading data: {e}"

        # schedule the next read_data call only if the system is not stopped
        window.after(1000, read_data)    

#sends a command to arduino via serial      
def send_command(ser, command):     

        try:
            ser.reset_input_buffer() #clear the gates
            ser.write((command + '\n').encode('utf-8')) #encode command in serial
            print(f"sent command: {command}") #debug line
            time.sleep(0.05)   #small delay for command processing

        except serial.SerialException as e:
            print(f"error sending command: {e}")

        except Exception as e:
            print(f"unexpected error in sending command: {e}")


# set up serial communication
def serial_setup(port="COM15", baudrate=9600, timeout=5):          
            
        try:
            ser = serial.Serial(port, baudrate, timeout=timeout)
            print(f"connected to arduino port: {port}")
            #lbl_monitor["text"] = f"connected to arduino port: {port}"
            time.sleep(1)   #make sure arduino is ready
            return ser
        except serial.SerialException as e:
            print(f"error: {e}")
            #lbl_monitor["text"] = f"error: {e}"
            return None
        finally:
            # Close serial connection
            if 'ser' in locals() and ser.is_open:
                ser.close()
                print("Serial port closed.")




###############        GUI PART       ###############

#ser = serial.Serial("COM13", baudrate=9600, timeout=5)
ser = serial_setup()

#initialize a new window
window = tk.Tk()
window.title("temperature chamber")
window.configure(bg="white")
window.wm_minsize(600, 750) # Minimum width of 650px and height of 800px

#prepare the general grid
#window.rowconfigure(0, minsize=600, weight=1)
#window.rowconfigure(1, minsize=600, weight=1)
window.columnconfigure(0, minsize=600, weight=1)
#window.columnconfigure(1, minsize=800, weight=1)


#monitor frame and content
frm_monitor = tk.Frame(window, borderwidth=1, highlightthickness=0, bg="white")
lbl_monitor = tk.Label(frm_monitor, text="arduino says things here", width=70, bg="white")
lbl_room = tk.Label(frm_monitor, text="current temperature", bg="white")
lbl_r_temp = tk.Label(frm_monitor, bd=1, width=45, relief="solid", bg="white")
lbl_desired = tk.Label(frm_monitor, text="desired temperature", bg="white")
lbl_d_temp = tk.Label(frm_monitor, bd=1, width=45, relief="solid", bg="white")
lbl_heater = tk.Label(frm_monitor, text="heater", bg="white")
lbl_cooler = tk.Label(frm_monitor, text="cooler", bg="white")
lbl_heater_status = tk.Label(frm_monitor, bd=1, width=45, relief="solid", bg="white")
lbl_cooler_status = tk.Label(frm_monitor, bd=1, width=45, relief="solid", bg="white")

#position update labels
lbl_room.grid(row=1, column=0, sticky="w", padx=5, pady=5)
lbl_r_temp.grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=5)

lbl_desired.grid(row=2, column=0, sticky="w", padx=5, pady=5)
lbl_d_temp.grid(row=2, column=1, columnspan=2, sticky="w", padx=5, pady=5)

lbl_heater.grid(row=3, column=0, sticky="w", padx=5, pady=5)
lbl_heater_status.grid(row=3, column=1, columnspan=2, sticky="w", padx=5, pady=5)

lbl_cooler.grid(row=4, column=0, sticky="w", padx=5, pady=5)
lbl_cooler_status.grid(row=4, column=1, columnspan=2, sticky="w", padx=5, pady=5)

#position monitor label
lbl_monitor.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)


#test frame & content & logo
frm_tests = tk.Frame(window, borderwidth=1, highlightthickness=0, bg="white")
# path to logo file 

image_path = "C:/Users/owenk/OneDrive/Desktop/Arduino/temperature chamber/temperature_chamber/interface/tkinter/arduino_logo.png"  
# use PIL to open the image
logo_image = Image.open(image_path)
logo_image = logo_image.resize((100, 100))  # adjust size
logo_photo = ImageTk.PhotoImage(logo_image)
#create  label for the image
lbl_image = tk.Label(frm_tests, image=logo_photo, bg="white")
lbl_image.image = logo_photo  # keep a reference to avoid garbage collection
lbl_image.grid(row=0, column=0, columnspan=3, sticky="nsew")  #position image


lbl_benchmark = tk.Label(frm_tests, text="BENCHMARK TESTS", bg="white")
btn_test1 = tk.Button(frm_tests, text="test 1", bg="white")
btn_test2 = tk.Button(frm_tests, text="test 2", bg="white")
btn_test3 = tk.Button(frm_tests, text="test 3", bg="white")
btn_run_all_benchmark = tk.Button(frm_tests, text="RUN ALL BENCHMARK TESTS", bg="white")
lbl_custom = tk.Label(frm_tests, text="CUSTOM TEST", bg="white")
ent_temp = tk.Entry(frm_tests, width=30, justify='left', bg="white", fg="black")
ent_temp.insert(0, "temperature in °C: ")
ent_duration = tk.Entry(frm_tests, width=30, justify='left', bg="white", fg="black")
ent_duration.insert(0, "duration in minutes: ")
btn_add_custom = tk.Button(frm_tests, text="ADD CUSTOM TEST", bg="white")
btn_run_custom = tk.Button(frm_tests, text="RUN CUSTOM TEST", bg="white")
btn_run_all_tests = tk.Button(frm_tests, text="RUN ALL TESTS", bg="white")
lbl_running = tk.Label(frm_tests, text="TEST RUNNING: ", bg="white")
lbl_running_info = tk.Label(frm_tests, bg="white")

#position labels, buttons and user input widgets in test frame
lbl_benchmark.grid(row=1, column=0, sticky="w", padx=5, pady=5)
btn_test1.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
btn_test2.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
btn_test3.grid(row=4, column=1, sticky="ew", padx=5, pady=5)
btn_run_all_benchmark.grid(row=5, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
lbl_custom.grid(row=6, column=0, sticky="w", padx=5, pady=5)
ent_temp.grid(row=7, column=1, sticky="ew", padx=5, pady=5)
ent_duration.grid(row=7, column=2, sticky="ew", padx=5, pady=5)
btn_add_custom.grid(row=8, column=1, sticky="ew", padx=5, pady=5)
btn_run_custom.grid(row=8, column=2, sticky="ew", padx=5, pady=5)
btn_run_all_tests.grid(row=10, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
lbl_running.grid(row=11, column=0, sticky="w", padx=5, pady=5)
lbl_running_info.grid(row=11, rowspan=3, column=1, columnspan=2, sticky="ew", padx=5, pady=10)

# create & position the STOP button to span across both columns
btn_stop = tk.Button(frm_tests, text="STOP", command=emergency_stop, bg="red", fg="white")
btn_stop.grid(row=15, column=0, columnspan=3, sticky="ew", padx=5, pady=5)  # Button spans across two columns

#position both frames
frm_tests.grid(row=0, column=0)
frm_monitor.grid(row=1, column=0, padx=5, pady=20)

#set data reading from serial every 0.5 second
window.after(500, read_data)

window.mainloop()