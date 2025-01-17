# reset
def reset():
    return {"commands": {"RESET": {}}}

# emergency stop
def emergency_stop():
    return {"commands": {"EMERGENCY_STOP": {}}}

# ping
def ping():
    return {"commands": {"PING": {}}}

# set temp & duration
def set_temp(data, override):
    return {"commands": {"SET_TEMP": data, "override": override}}

# handshake
def handshake(time):
    return {"handshake": {"timestamp": time}}

# get test queue
def get_test_queue():
    return {"commands": {"GET_TEST_QUEUE": {}}}

# run all tests
def run_all_tests():
    return {"commands": {"RUN_QUEUE": {}}}

