# set up serial communication
def serial_setup(port='COM15', baudrate=9600, timeout=5, lbl_monitor = None): # adjust port if necessary
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        print(f'connected to arduino port: {port}')
        if lbl_monitor:
                lbl_monitor['text'] = f'connected to arduino port: {port}'
        time.sleep(1)  # make sure arduino is ready
        return ser
    except serial.SerialException as e:
        print(f'error: {e}')
        if lbl_monitor:
                lbl_monitor['text'] = f'error: {e}'
        return None


# read all serial output
def capture_all_serial():
    global is_stopped
    global starting

    if not is_stopped:  # only read data if the system is not stopped
        if ser and ser.is_open:
            try:
                # read the entire response from the Arduino
                response = ser.readline().decode('utf-8').strip()

                if response:
                    # print the entire response (debugging, regular data, etc.)
                    #print(f'from serial: {response}')

                    # make a list of trigger responses
                    trigger_responses = ['Setting', 'Running', 'Test complete', 'Target temp', 'Sequence complete']
# RUNNING IN TOP ROW IN BOLD OR SOMETHING WHILE ALL THE OTHERS SCROLL BELOW

                    # display the response in the listbox if triggered
                    if any(response.strip().startswith(trigger) for trigger in trigger_responses):
                        starting = True # set flag to True
                        print(response)
                        listbox.insert(tk.END, response)  # insert the response into the listbox
                        listbox.yview_moveto(1)   # move the view to the last line (bottom)
                        starting = False  # reset flag after receiving a response so listbox doesn't keep updating

                else:
                    # handle case where no valid data was received
                    print('no valid data received')


            except serial.SerialException as e:
                # handle serial communication errors
                print(f'error reading serial data: {e}')


        # schedule the next serial capture after 3 seconds
        window.after(3000, capture_all_serial)


# read data from serial
def read_data():
    global is_stopped
    global starting

    if not is_stopped:  # only read data if the system is not stopped
        if ser and ser.is_open:
            try:
                send_command(ser, 'SHOW DATA')  # send command to request data

                response = ser.readline().decode('utf-8').strip()  # decode serial response

                if response:
                    #print(f'arduino responded: {response}')
                    if lbl_monitor:
                        lbl_monitor['text'] = f'{response}'

                else:
                    print('received unexpected message or no valid data')
                    if lbl_monitor:
                        lbl_monitor['text'] = 'received unexpected message or no valid data'

            except serial.SerialException as e:
                print(f'error reading data: {e}')
                if lbl_monitor:
                    lbl_monitor['text'] = f'error reading data: {e}'

        # schedule the next read_data call only if the system is not stopped
        window.after(1000, read_data) # run this method every 1 sec


# sends a command to arduino via serial
def send_command(ser, command):
    try:
        ser.reset_input_buffer()  # clear the gates
        ser.write((command + '\n').encode('utf-8'))  # encode command in serial
        print(f'sent command: {command}')  # debug line
        time.sleep(0.02)  # small delay for command processing

    except serial.SerialException as e:
        print(f'error sending command: {e}')

    except Exception as e:
        print(f'unexpected error in sending command: {e}')


# emergency stop
def emergency_stop():
    global is_stopped
    is_stopped = True  # set flag to stop the read_data loop

    command = 'EMERGENCY STOP'
    send_command(ser, command)
    lbl_monitor['text'] = 'EMERGENCY STOP'
    clear_entry_on_stop()
    listbox.delete(0, tk.END)  # clear the listbox
    listbox.insert(0, 'EMERGENCY STOP')