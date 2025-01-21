# Temperature Chamber
This project is a PyQt5-based application for controlling and monitoring a temperature chamber. It includes functionalities to select ports, start tests, monitor temperature and test progress, and handle emergency stops.


## Key Use Case
The goal of this chamber is to create a standardised mechanism as well as a benchmark
to measure boards against. The chamber is a tool for answering questions like "How long can a board
operate at 60°C before failure?" It prioritizes accessibility and replicability by using cost-effective,
off-the-shelf components.

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

## Firmware
The firmware for the temperature chamber includes the following:
- A state machine to manage states such as ```HEATING```, ```COOLING```, ```RESET```, ```REPORT```, and ```EMERGENCY STOP```. (see [activity diagram](https://github.com/defliez/temperature_chamber/blob/main/docs/state-machine-activity-diagram.pdf)).
- A test running system that allows the running of established benchmark tests as well as your own custom made tests.
- Queueing system to be able to queue several tests at a time, as well as clear the queue.
- Channels for communicating with the temperature chamber from an external application via the defined Communication Protocol (see [docs](https://github.com/defliez/temperature_chamber/blob/main/docs/docs.md)).
- Robust error handling including emergency stop in case of serial disconnections.
- Real-time serial updates on temperature, tests status, queued tests and machine state.
- Infrastructure to communicate with external applications via a defined communication protocol (see [docs](https://github.com/defliez/temperature_chamber/blob/main/docs/docs.md)).

## Desktop application
The Temperature Chamber can be controlled and monitored from a desktop application, made in Python & PyQt5.
The desktop application for the Temperature Chamber includes:
- A user-friendly GUI for controlling the temperature chamber.
- Real-time temperature and test monitoring.
- Queue tab for managing the test queue with JSON file handling, as well as clearing the test queue.
- Tab for manual control of the chamber, allowing for temperature and duration to be set.
- Logging and error handling.
- Infrastructure to communicate with the Arduino control board for the Temperature Chamber via a defined communication protocol (see [docs](https://github.com/defliez/temperature_chamber/blob/main/docs/docs.md)).





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

## Safety measures
The Temperature Chamber system has mechanisms to ensure safe usage.

### Temperature thresholds
The firmware defines an upper limit of of 100°C for setting the temperature - both in tests and manual control. 

### Ping signals and timers
The control board for the chamber regularly sends ping signals to the Python app, and receives a ping response. In the case that the control board doesnt receive a ping signal for more than 5 minutes, the test and machine states will be reset and the Temperature Chamber will go into `EMERGENCY_STOP` state. This is also communicated via the LCD on the Chamber. A timer of 5 minutes is also present in the Python app, which triggers a popup message telling the operator that connection has been lost and the Chamber has gone into `EMERGENCY STOP` state. The python will notify the operator if serial connection has been lost to either boards, control board or test board, after 15 seconds of no ping, so that the Chamber doesn't reset without the operators knowledge that serial connection had been lost.


## Acknowledgments:
- **Adam Harb**
    - Hardware design, the custom shield, and the original state machine implementation.
- **Valentino Glave**
    - Modernized and optimized existing state machine.
    - Implemented state machine and infrastructure to queue and run tests.
    - Optimized existing functionality in firmware.
    - Defined communication protocol.
    - Integrated remote control on firmware side.
    - Enhanced workflows.


- **Owen Kraus**
    - Creating a functional and user friendly Python application.
    - Integrated remote control on software side.

For inquiries or further development, please contact via the provided channels.

Authors:
* Valentino Glave, <valentinoglave@protonmail.com>
* Owen Kraus, <owenkraus9@gmail.com>
 * Adam Harb, <adam.harb@hotmail.com>
 * David Cuartielles, <d.cuartielles@arduino.cc>

 (cc-sa-by-nc) 2024 Arduino, Sweden

