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
def add_custom():
    
    test_data = open_file()

    if test_data is not None:
        #get input and clear it of potential empty spaces
        temp_string = ent_temp.get().strip()
        duration_string = ent_duration.get().strip()

         # Initialize temp and duration
        temp = None
        duration = None
        is_valid = True  # track overall validity

        if temp_string:
            try:
                temp = float(temp_string)
                if temp >= 100:
                    print('max 100')
                    ent_temp.delete(0, tk.END)  # clear the entry
                    ent_temp.insert(0, "max temperature = 100°C")  # show error message in entry
                    is_valid = False
     
            except ValueError:
                print('numbers only')
                ent_temp.delete(0, tk.END)  # clear the entry
                ent_temp.insert(0, "numbers only")  # show error message in entry
                is_valid = False
        else:
                print("no temperature input")
                ent_temp.delete(0, tk.END)  # clear the entry
                ent_temp.insert(0, "enter a number")  # show error message in entry
                is_valid = False 

        if duration_string:    
            try:
                duration = int(duration_string)
                if duration < 1:  # check for a minimum duration 
                    print('minimum duration is 1')
                    ent_duration.delete(0, tk.END)
                    ent_duration.insert(0, "minimum duration = 1 minute")
                    is_valid = False 
            except ValueError:
                print('numbers only')
                ent_duration.delete(0, tk.END)  # clear the entry
                ent_duration.insert(0, "numbers only")  # show error message in entry
                is_valid = False         
        else:
            print('no valid duration')
            ent_duration.delete(0, tk.END)  # clear the entry
            ent_duration.insert(0, "enter a number")  # show error message in entry
            is_valid = False

        # check if both entries are valid before proceeding
        if is_valid and temp is not None and duration is not None:
            new_sequence = {"temp": temp, "duration": duration}
            test_data["custom"].append(new_sequence)  # append new custom test
            save_file(test_data)  # save back to json file
            print('custom test added successfully')
        else:
            print("Cannot add custom test due to invalid inputs.")

    else:
            print("unable to add custom test due to file loading error")


'''
#pick your test method
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
              custom_test = test_data.get("custom", [])
              send_json_to_arduino(custom_test)'''

def run_custom():  
    test_data = open_file()     
    # extract only the custom tests 
    custom_test = test_data.get("custom", [])
    if custom_test:
        send_json_to_arduino(custom_test)
    else:
        print('no custom tests on file')


