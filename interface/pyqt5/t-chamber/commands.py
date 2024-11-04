from datetime import datetime


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


'''
{"handshake":
    {
        "timestamp":"2157-11-01T10:37:47",
        "current_state":"EMERGENCY_STOP",
        "last_shutdown_cause":"Unknown",
        "last_heat_time":"N/A"
    }
}

PING
{
    "ping_response": {
        "alive": true,
        "timestamp": "2024-11-01T10:31:47",
        "machine_state": "REPORT",
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