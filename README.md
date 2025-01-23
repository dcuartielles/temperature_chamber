# Temperature Chamber
The Temperature Chamber is a complete system for benchmark testing and stress-testing electronic boards in a controlled thermal environment. It combines accessible hardware, advanced firmware, and a Python-based desktop application to achieve precise temperature control, test execution, and real-time monitoring. The system is designed to standardize thermal testing while prioritizing accessibility and replicability with cost-effective, off-the-shelf components.


## Key Use Case
The goal of this chamber is to create a standardised mechanism as well as a benchmark
to measure boards against. The chamber is a tool for answering questions like "How long can a board
operate at 60°C before failure?" It prioritizes accessibility and replicability by using cost-effective,
off-the-shelf components.

---

## Hardware
The physical chamber consists of:
- a case sourced from a musical instrument
- a natural cork for isolation, a ceramic heating element
- an air-blower for cooling 
- two 1-wire thermocouple sensors
- an Arduino Uno R4 Wifi to control the relays and sensor inside of the chamber
- a custom PCB shield including solid-state relays for heater and blower
- an lcd to display temperature inside the chamber, set goal temperature of running test or manual sequence, and emergency stops caused by potential disconnections

The hardware allows for the temperature to safely reach and maintain up to 100°C.

---

## Firmware
The firmware manages the chamber's operation, focusing on safety, precision, and flexibility. Key features include:

### State Machine
The firmware operates via a state machine with the following states:
- **HEATING**: Activates the heater to raise the temperature.
- **COOLING**: Activates the blower to lower the temperature.
- **IDLE**: Chamber stays in idle mode until a condition is met or further input is provided.
- **EVALUATE**: Evaluates whether to go into **COOLING** or **HEATING** state based on temperature.
- **EMERGENCY_STOP**: Shuts down operations until the start switch is switched on.

### Test Execution
The chamber supports:
- Running predefined and custom tests.
- Queueing multiple tests with parameters such as temperature and duration
- Real-time monitoring of test progress.

### Communication protocol
The firmware communicates with the desktop application via a JSON-based protocol, enabling:
- Remote control of the chamber.
- Sending and receiving commands like `PING`, `RESET`, `SET_TEMP`, and `RUN_QUEUE`.
- Handshake and ping for connection validation and error handling.
- Real-time feedback on test status, temperature, and machine state.
See [docs](https://github.com/defliez/temperature_chamber/blob/main/docs/docs.md) for more information.

### Error handling
- Timeout mechanisms to reset and cool down the chamber after prolonged connection loss.
- Safety measures for exceeding temperature limits.

---

## Desktop application
The Python-based desktop application provides an intuitive interface to interact with the chamber:

### Features
- **Real-time Monitoring**: View the current temperature, test progress, and machine state.
- **Queue Management**: Upload JSON test configurations, manage test queues, and clear tests.
- **Manual Control**: Set temperature and duration manually, overriding queued tests.
- **Wifi Boards**: Option to connect a microcontroller with Wifi capabilities to test the Wifi performance of microcontrollers being tested.
- **Error Notifications**: Alerts for connection issues, emergency stops, and test interruptions.
- **Logging**: Detailed logs for debugging and analysis.

## Installation
1. Clone the repository:
```sh
git clone https://github.com/defliez/temperature_chamber.git
cd temperature_chamber
```

2. Install the dependencies:
```sh
pip install pyqt5 python-dateutil pyserial
```

## Usage
1. Run the application:
```sh
python3 interface/pyqt5/t-chamber/main.py
```

2. Using the GUI:
- Select the control and test board ports.
- Click refresh to update the connected ports in case of disconnection.
- Click the `Start` button to establish serial connection with the boards.
- Enter the `Queue tab` to queue tests, see the current queued tests and clear the test queue.
- Enter the `Manual tab` to manually set the temperature and duration, overriding potential running tests.
- Enter the `Running test info` tab to view:
    - Status updates from the chamber.
    - Expected output and real-time actual output from the test board.
    - An overview of the current test and sequence status, including:
    - Current test name.
    - Amount of sequences in the current test.
    - Remaining time of the running sequence.
    - Total amount of sequences across all queued tests (visualized with segmented progress bar).
    - Estimated running time of queued tests, taking into account the set durations for the sequences as well as the time to heat up and cool down the chamber between sequences.
- Press `reset control board` to clear all tests in the queue, interrupt the current running test, and put the Temperature Chamber into an idle state.

---

## Safety measures
- **Temperature Thresholds**: Prevents the chamber from exceeding 100°C. This limit can be temporarily overridden.
- **Ping Mechanism**: Ensures continuous connection between the chamber and application. 
- **Emergency Stop**: Resets and cools down the chamber after 5 minutes of no ping response.

---

## Acknowledgments:
- **Adam Harb**:
    - Hardware design, the custom shield, and the original state machine implementation.
- **Valentino Glave**:
    - Enhanced the firmware with JSON-based communication for remote control and monitoring.
    - Modernized and optimized the state machine for advanced test handling.
    - Integrated remote control on firmware side.
    - Implemented functionality and UI components to allow connection to a Wifi board.
    - Refactored UI to enhance responsiveness.
    - Integrated robust error handling and logging.
    - Enhanced workflows.
- **Owen Kraus**:
    - Created an intuitive and functional Python application.
    - Developed infrastructure to communicate with, and display output from the chamber.
    - Implemented robust error handling and logging.

For inquiries or further development, please contact via the provided channels.

Authors:
- Valentino Glave, <valentinoglave@protonmail.com>
- Owen Kraus, <owenkraus9@gmail.com>
- Adam Harb, <adam.harb@hotmail.com>
- David Cuartielles, <d.cuartielles@arduino.cc>

---

 (cc-sa-by-nc) 2024 Arduino, Sweden

