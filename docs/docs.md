# Temperature Chamber Communicaton Protocol
The communication protocol is JSON based. It includes standards for sending and receiving pings and handshakes, sending commands, receiving updates for test status & machine state as well as queueing and running defined benchmark tests and custom tests.


To send tests from the Python application to be queued and run in the Temperature chamber, the user uploads a json file with meta data for the tests. The meta data consists of:

## Tests 
- Tests are sent from the Python application to be queued and run in the Temperature Chamber.
- Each test includes:
    - Test names as the key for each test.
    - An array of chamber sequences, each specifying a temperature and duration.
    - The path for the sketch to be uploaded to the board inside the chamber.
    - A string value of the expected serial output from the board inside the chamber.

Tests are defined in test configuration files, which are put in designated directories inside of the `tests` directory, alongside directories for sketches that are to be uploaded to the board inside of the chamber for each test configuration.

### File Structure for Tests
Below is an example to showcase how tests should be placed inside the `tests` directory. In this example:
- `alphabets` is a directory designated to a defined test suite.
- `alphabet` and `alphabet_mathematical` are directories to store sketches that are to be compiled and uploaded to test boards as part of the current test suite.
- `alphabet_test.json` is a test configuration file that specifies the tests that are to be run as part of the test suite.

```sh
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

## Commands
- Commands are sent from the Python app to control various functionalities of the Temperature Chamber, as well as to retrieve data about the state of the chamber and the tests.
- Common commands include:
    - `PING` - to check if the connection is alive, and to receive information about the state of the machine.
    - `RESET` - to reset the system, interrupting any running test and clearing the test queue.
    - `EMERGENCY_STOP` - to reset the system, clear the test queue and initiate a cooldown process that brings the temperature inside the chamber down to room temperature.
    - `SET_TEMP` - to set the temperature and duration manually, without a test configuration file.
    - `GET_TEST_QUEUE` - to retrieve the current test queue loaded in the Temperature Chamber.
    - `RUN_QUEUE` - to run the queued tests.

### Example Commands from Python App
```json
{
    "commands": {
        "PING": {},
        "RESET": {},
        "EMERGENCY STOP": {},
        "SET_TEMP": { "temp": 40, "duration": 300000 },
        "GET_TEST_QUEUE": {},
        "RUN_QUEUE": {},
    }
}
```

## Handshake
- A handshake is used to establish initial communication between the Python app and the Temperature Chamber.
- It includes a timestamp and other relevant data.

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
        "machine_state": "RESET",
        "last_shutdown_cause": "Lost connection",
        "last_heat_time": "2024-12-05T13:00:00"
    }
}
```

## Ping
- Ping messages are used to ensure continuous communication and system health checks. 
- System fail-safes are in place to warn operators of temporary loss of connection, and safe system resetting and shutdown in case of no ping response for more than 5 minutes.

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
        "machine_state":"RESET",
        "current_temp":35.625,
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
