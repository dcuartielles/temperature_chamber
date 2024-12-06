# Arduino Temperature Chamber

## Description
The goal of the Temperature Chamber is to create a standardised mechanism as well as a benchmark to measure boards against. The chamber is a tool for answering questions like "How long can a board operate at 60C before failure?" It prioritizes accessibility and replicability by using cost-effective, off-the-shelf components.

## Tests 
To send tests from the Python application to be queued and run in the Temperature chamber, the user uploads a json file with meta data for the tests. The meta data consists of:
- Test names as the key for each test.
- An array of chamber sequences, each including keys and values for temperature and duration.
- A path for the sketch that is to be uploaded to the board inside of the chamber.
- A string value of the expected serial output from the board inside of the chamber.

These files are put in designated directories inside of the `tests` directory, alongside directories for sketches that are to be uploaded to the board inside of the chamber for each test configuration.

### Example file structure:
```sh
tests
|-- alphabets
|   |-- alphabet
|   |   `-- alphabet.ino
|   |-- alphabet_mathematical
|   |   `-- alphabet_mathematical.ino
|   `-- alphabet_test.json
```

### Example test configuration file:
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

### Example ping from Python app:
```json
{ "commands": "PING": {} }
```

### Example ping from Temperature Chamber:
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

### Example handshake from Python app.
```json
{
    "handshake": {
        "timestamp": "2024-12-05T15:21:06"
    }
}
```

### Example handshake from Temperature Chamber:
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

### Example test sketch:
```arduino
void setup() {
    Serial.begin(9600);
}

void loop() {
    // Loop through the alphabet
    for (char letter = 'A'; letter <= 'Z'; letter++) {
        Serial.print(letter);
        delay(500);
    }

    // Print a newline after the full alphabet
    Serial.println();
    delay(1000);
}
```
