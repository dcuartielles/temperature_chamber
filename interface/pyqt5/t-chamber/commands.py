
# show data
def show_data():
    show_data = {"commands": {
                "SHOW_DATA": {}
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

# interrupt test
def interrupt_test():
    interrupt = {"commands": {
            "INTERRUPT_TEST": {}
            }
    }
    return interrupt

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


# set temp & duration
def set_temp(data):
    set_all = {"commands": {
            "SET_TEMP": data
            }
    }
    return set_all

def handshake(time):
    hand = {"handshake":
        {
            "timestamp": time
        }
    }
    return hand



'''
PING
{
    "ping_response": {
        "alive": true,
        "timestamp": "2024-11-01T10:31:47",
        "machine_state": "REPORT",
        "current_temp": 423,
        "test_status": {
            "is_test_running": false,
            "current_test": "",
            "current_sequence": 1,
            "desired_temp": -41,
            "current_duration": 0,
            "time_left": 120
        }
    }
}
'''