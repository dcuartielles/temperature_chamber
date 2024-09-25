import tkinter as tk
import serial
import time


# Global flag for stopping the reading process
is_stopped = False

#set temperature (user input)
def set_temp():
    
    global is_stopped
    is_stopped = False #set flag to restart the read_data loop
    
    temperature = ent_temp.get()

    if temperature.replace('.', '', 1).isdigit():
           command = f"SET TEMP {float(temperature):.2f}"
           send_command(ser, command)
           lbl_monitor["text"] = f"desired temperature is set to {float(temperature):.2f} \N{DEGREE CELSIUS}"
           window.after(3000, read_data)
    

    else:
           lbl_monitor["text"] = "digits only"

# emergecy stop
def emergency_stop():
    global is_stopped
    is_stopped = True #set flag to stop the read_data loop

    command = "EMERGENCY STOP"
    send_command(ser, command)
    lbl_monitor["text"] = "EMERGENCY STOP"
  

#read data from serial
def read_data():
    global is_stopped

    if not is_stopped:  # only read data if the system is not stopped
        if ser and ser.is_open:
            try:
                send_command(ser, "SHOW DATA")  # Send command to request data
                time.sleep(0.1)  # Wait for Arduino to process the command

                response = ser.readline().decode('utf-8').strip()

                if response:
                    print(f"arduino responded: {response}")
                    lbl_monitor["text"] = f"{response}"
                else:
                    print("received unexpected message or no valid data.")
                    lbl_monitor["text"] = "received unexpected message or no valid data."

            except serial.SerialException as e:
                print(f"Error reading data: {e}")
                lbl_monitor["text"] = f"Error reading data: {e}"

        # Schedule the next read_data call only if the system is not stopped
        window.after(500, read_data) 
            
            

#sends a command to arduino via serial      
def send_command(ser, command):     

        try:
            ser.reset_input_buffer() #clear the gates
            ser.write((command + '\n').encode('utf-8')) #encode command in serial
            print(f"sent command: {command}") #debug line
            time.sleep(1)   #small delay for command processing

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



#ser = serial.Serial("COM13", baudrate=9600, timeout=5)
ser = serial_setup()

#initialize a new window
window = tk.Tk()
window.title("temperature monitor")

window.rowconfigure(0, minsize=250, weight=1)
window.columnconfigure(1, minsize=800, weight=1)


lbl_monitor = tk.Label(window, text="arduino says things here")
frm_buttons = tk.Frame(window, relief=tk.RAISED, bd=2)
btn_stop = tk.Button(master=frm_buttons, text="STOP THE OVEN", command=emergency_stop)
btn_enter = tk.Button(master=frm_buttons, text="SET TEMPERATURE", command=set_temp)
ent_temp = tk.Entry(master=frm_buttons, width=30)


btn_stop.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
btn_enter.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
ent_temp.grid(row=2, column=0, padx=5)

frm_buttons.grid(row=0, column=0, sticky="ns")
lbl_monitor.grid(row=0, column=1, sticky="nsew")

#set data reading from serial every 0.5 second
window.after(100, read_data)

window.mainloop()