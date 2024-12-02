# reset
def reset():
    reset_command = {"commands": {
            "RESET": {}
            }
    }
    return reset_command


# emergency stop
def emergency_stop():
    stop = {

        "commands": {
            "EMERGENCY_STOP": {}
        }
    }
    return stop


# ping
def ping():
    ping_command = {
        "commands": {
            "PING": {

            }
        }
    }
    return ping_command


# set temp & duration
def set_temp(data):
    set_all = {"commands": {
            "SET_TEMP": data
            }
    }
    return set_all


# handshake
def handshake(time):
    hand = {"handshake":
        {
            "timestamp": time
        }
    }
    return hand

# get test queue
def get_test_queue():
    get_queue = {"commands": {
           "GET_TEST_QUEUE": {
            }
        }
    }
