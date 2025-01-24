# Temperature Chamber Communicaton Protocol

The communication protocol is JSON based and defines standards for sending and receiving pings, handshakes, commands, and updates about test status, machine state and queued tests. This enables remote control and monitoring of the Temperature Chamber.

---

## Tests 

Tests are sent from the Python application to be queued and run in the Temperature Chamber.

Each test includes:
- **Test name**: A unique identifier for the test.
- **Chamber sequences**: An array of phases, each specifying a target temperature and a duration.
- **Sketch path**: The path ot the sketch to be uploaded to the Arduino board inside the chamber.
- **Expected output**: A string representing the expected serial output from the test board.

Tests are defined in test configuration files located within the `tests` directory. Each directory contains:
- Test configurations (`*.json`).
- Sketches to be uploaded to the board inside the chamber.

### File Structure for Tests

Below is an example structure for organizing test-related files withing the `tests` directory:

```
tests
|-- alphabets
|   |-- alphabet
|   |   `-- alphabet.ino
|   |-- alphabet_mathematical
|   |   `-- alphabet_mathematical.ino
|   `-- alphabet_test.json
```

### Example Test Configuration File:

```json
{
    "tests": {
        "first_alphabet_low_temp": {
            "chamber_sequences": [
                { "temp": 38, "duration": 60000 }
            ],
            "sketch": "./alphabets/alphabet/alphabet.ino",
            "expected_output": "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        },
        "match_alphabet_low_to_high_temp": {
            "chamber_sequences": [
                { "temp": 48, "duration": 90000 },
                { "temp": 80, "duration": 300000 }
            ],
            "sketch": "./alphabets/alphabet_mathematical/alphabet_mathematical.ino",
            "expected_output": "ABCDEFGHIJKLMNOPQRSTUVWXYZ120"
        },
        "alphabet_high_to_low": {
            "chamber_sequences": [
                { "temp": 70, "duration": 60000 },
                { "temp": 50, "duration": 120000 }
            ],
            "sketch": "./alphabets/alphabet/alphabet.ino",
            "expected_output": "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        }
    }
}
```
---

## Commands
Commands allow the Python app to control the chamber and retrieve data. The available commands include:
- `PING`: Checks if the connection is alive and retrieves the machine state and test status.
- `RESET`: Resets the system, interrupting running tests, and clears the test queue.
- `EMERGENCY_STOP`: Resets the system, clears the queue, and initiates a cooldown to room temperature.
- `SET_TEMP`: Manually sets a target temperature and duration. Includes an optional override flag for exceeding default limits.
- `GET_TEST_QUEUE`: Retrieves the current test queue from the chamber.
- `RUN_QUEUE`: Starts the queued tests.

### Example Commands from Python App:

```json
{
    "commands": {
        "PING": {},
        "RESET": {},
        "EMERGENCY STOP": {},
        "SET_TEMP": { "temp": 40, "duration": 300000, "override": false },
        "GET_TEST_QUEUE": {},
        "RUN_QUEUE": {}
    }
}
```

---

## Handshake
The handshake establishes initial communication between the Python ap and the Temperature Chamber. It synchronizes system state and provides a timestamp.

### Example Handshake from Python App:
```json
{
    "handshake": {
        "timestamp": "2024-12-05T15:21:06"
    }
}
```

### Example Handshake from Temperature Chamber:
```json
{
    "handshake": {
        "timestamp": "2024-12-05T15:21:06",
        "machine_state": "IDLE",
        "last_shutdown_cause": "Lost connection",
        "last_heat_time": "2024-12-05T13:00:00"
    }
}
```

---

## Ping
Ping ensures continuous communication between the Python app and the chamber. A lack of ping response triggers an emergency stop after 5 minutes.

### Example Ping from Python App:

```json
{ "commands": "PING": {} }
```

### Example Ping from Temperature Chamber:

```json
{
    "ping_response": {
        "alive":true,
        "timestamp":"2024-12-05T15:11:55",
        "machine_state":"HEATING",
        "current_temp":30.625,
        "test_status": {
            "is_test_running":true,
            "current_test":"alphabet_38",
            "current_sequence":1,
            "desired_temp":35,
            "current_duration":60000,
            "time_left":37,
            "queued_tests":3
        }
    }
}
```
