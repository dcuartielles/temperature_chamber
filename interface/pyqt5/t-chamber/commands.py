from datetime import datetime


# show data
def show_data():
    show_data = {"commands": {
                "SHOWDATA": {}
                }
    }
    return show_data

# reset
def reset():
    reset = {"commands": {
            "RESET": {}
            }
    }
    return reset

# emergency stop
def emergency_stop():
    stop = {"commands": {
            "EMERGENCY_STOP": {}
            }
    }
    return stop

# ping
def ping():
    ping = {
        "commands": {
            "PING": {

            }
        }
    }
    return ping

# handshake
def handshake():
    time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    time_string = f'"timestamp”:"{time}"'
    handshake = {
        "commands": {
            "HANDSHAKE": {
                time_string
            }
        }
    }
    return handshake

# set temp & duration
def set_temp(data):
    set_all = {"commands": {
            "SET_TEMP": {
                data
            }
            }
    }
    return set_all
