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
     
           
'''
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
                    lbl_monitor["text"] = f"current temperature: {room_temp}°C | desired temperature: {desired_temp}°C | heater {'ON' if heater_status else 'OFF'} | cooler {'ON' if cooler_status else 'OFF'}"
                    lbl_r_temp["text"] = f"{room_temp}°C"
                    lbl_d_temp["text"] = f"{desired_temp}°C"
                    lbl_heater["bg"] = f"{'green' if heater_status else 'red'}"
                    lbl_cooler["bg"] = f"{'blue' if cooler_status else 'orange'}"
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

#prepare the general grid
window.rowconfigure(0, minsize=600, weight=1)
window.rowconfigure(1, minsize=130, weight=1)
window.columnconfigure(0, minsize=600, weight=1)
window.columnconfigure(1, minsize=400, weight=1)


#monitor & logo frame and content
frm_monitor = tk.Frame(window, borderwidth=1, highlightthickness=0, bg="white")
lbl_monitor = tk.Label(frm_monitor, text="arduino says things here")
lbl_room = tk.Label(frm_monitor, text="current temperature")
lbl_r_temp = tk.Label(frm_monitor)
lbl_desired = tk.Label(frm_monitor, text="desired temperature")
lbl_d_temp = tk.Label(frm_monitor)
lbl_heater = tk.Label(frm_monitor, text="heater")
lbl_cooler = tk.Label(frm_monitor, text="cooler")

# path to logo file 
image_path = "C:/Users/owenk/OneDrive/Desktop/Arduino/temperature chamber/temperature_chamber/interface/tkinter/arduino_logo.jpg"  
# use PIL to open the image
logo_image = Image.open(image_path)
logo_image = logo_image.resize((90, 90))  # adjust size
logo_photo = ImageTk.PhotoImage(logo_image)
#create  label for the image
lbl_image = tk.Label(frm_monitor, image=logo_photo)
lbl_image.image = logo_photo  # keep a reference to avoid garbage collection
lbl_image.grid(row=0, column=0, sticky="nsew", padx=5, pady=35)  #position image

#button frame & content
frm_buttons = tk.Frame(window, borderwidth=1, highlightthickness=0, bg="white")
btn_stop = tk.Button(master=frm_buttons, text="STOP", command=emergency_stop, bg="red", fg="white", width=30, height=13)
btn_enter = tk.Button(master=frm_buttons, text="SET TEMPERATURE", command=set_temp)
ent_temp = tk.Entry(master=frm_buttons, width=30, justify='center')


#position buttons and user input widget
btn_stop.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
btn_enter.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
ent_temp.grid(row=1, column=0, padx=5, pady=5)

# Position the STOP button to span across both columns
btn_stop.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)  # Button spans across two columns
btn_enter.grid(row=1, column=0, sticky="ew", padx=5, pady=5)  # Button in first column
ent_temp.grid(row=2, column=0, padx=5)  # Entry in first column

#position monitor label
lbl_monitor.grid(row=0, column=0, sticky="w", padx=35, pady=35)

#position update labels
lbl_room.grid(row=1, column=0, sticky="w", padx=35, pady=35)
lbl_r_temp.grid(row=1, column=1, sticky="w", padx=35, pady=35)

lbl_desired.grid(row=2, column=0, sticky="w", padx=35, pady=35)
lbl_d_temp.grid(row=2, column=1, sticky="w", padx=35, pady=35)

lbl_heater.grid(row=3, column=0, sticky="w", padx=35, pady=35)
lbl_cooler.grid(row=3, column=1, sticky="e", padx=35, pady=35)

#position both frames
frm_buttons.grid(row=0, column=0, sticky="ns")
frm_monitor.grid(row=0, column=1, sticky="nsew")

#set data reading from serial every 0.5 second
window.after(500, read_data)

window.mainloop()