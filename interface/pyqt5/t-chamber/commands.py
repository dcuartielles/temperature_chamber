# show data
def show_data():
    show_data = {"commands": {
                "SHOW DATA": {}
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
            "PING": {}
        }
    }
    return ping

# handshake
def handshake():
    handshake = {
        "commands": {
            "HANDSHAKE": {}
        }
    }
    return handshake
