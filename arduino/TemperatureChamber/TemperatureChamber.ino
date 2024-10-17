/*
   Board heater
   Ver. 0002

   The board heater is a laboratory instrument consisting of a chamber with
   a ceraminc heating element, an air blower, and 1-wire thermocouple sensors.
   The chamber can reach over 100 deg C at constant pressure and volume. It doesn't,
   however, allow for controlling the humidity.

   The goal of this chamber is to create a standardised mechanism as well as a benchmark
   to measure boards against. We want to be able of answering questions such as: for how
   long can a board work at 60 deg C before failing. At the same time, the design should be
   inexpensive, thus making it accessible and easy to replicate.

   The first version of the artifact runs on a traditional Arduino Uno, with a specially made
   shield including some solid-state relays to control both the blower and the heating element. While
   the heating element can be obtained easily from any electronics catalogue, the blower was
   recycled from a different artifact (an inflatable mattress) because it has the ability to
   stop the airflow mechanically when not pumping. If any other blower should be considered, this
   will be of importance.

   The structure of this code is a state machine that allows for either direct interaction with
   the physical controls on the device, or to have full remote control via serial communication. This
   is a standard state machine design by D. Cuartielles, it can be found at many other places.

   Adam designed the machine, created the shield, and wrote the original code this state machine 
   is based on. For further information, use the emails below.

Authors:
 * Adam Harb, <adam.harb@hotmail.com>
 * Valentino Glave, defliez@protonmail.com
 * David Cuartielles, d.cuartielles@arduino.cc

 (cc-sa-by-nc) 2024 Arduino, Sweden

 */

// Include Libraries
#include <DallasTemperature.h>
#include <OneWire.h>
#include <LiquidCrystal_I2C.h>
#include <EduIntro.h>
#include<ArduinoJson.h>

// Defines
#define ONE_WIRE_BUS_1      A0  // temp sensor 1
#define ONE_WIRE_BUS_2      A1  // temp sensor 2
#define RELAY_COOLER        2
#define RELAY_HEATER        3
#define BUTTON_INCREMENT    5
#define BUTTON_DECREMENT    4
#define SWITCH_START        6
#define SWITCH_SYSTEM_STATE 7

// States for the state machine
#define RESET               0
#define HEATING             1
#define COOLING             2
#define REPORT              3
#define EMERGENCY_STOP      4

// Modes for the state machine
#define AUTOMATIC           0
#define MANUAL              1

// Define temperature limits
#define TEMPERATURE_MAX     100
#define TEMPERATURE_MIN     0


// Verbosity levels (for serial) - LOW and HIGH already exist, therefore commented
//#define LOW 0
#define MEDIUM 2
//#define HIGH 1

// Setup OneWire instances to communicate with any OneWire devices
OneWire oneWire1(ONE_WIRE_BUS_1);
OneWire oneWire2(ONE_WIRE_BUS_2);

// Pass the oneWire references to DallasTemperature
DallasTemperature sensors1(&oneWire1);
DallasTemperature sensors2(&oneWire2);

// Instantiate the lcd
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Instantiate the buttons
Button buttonIncrease(BUTTON_INCREMENT);
Button buttonDecrease(BUTTON_DECREMENT);

// Instantiate the switches
Button switchStart(SWITCH_START);
Button switchSystem(SWITCH_SYSTEM_STATE);

// Instantiate the relays
Led cooler(RELAY_COOLER);
Led heater(RELAY_HEATER);

// Timing variables
unsigned long timerHeater = 0;
unsigned long timerCooler = 0;
unsigned long PeriodHeater = 0;
unsigned long PeriodCooler = 0;

// Heater and cooler states
int stateHeater = 0;
int stateCooler = 0;


// State machine variables
int stateHeaterOld = 0;
int stateCoolerOld = 0;
int dutyCycleHeater = 0;
int dutyCycleCooler = 0;
int status = EMERGENCY_STOP;
bool dataEvent = false;

struct Sequence {
    float targetTemp;
    unsigned long duration;
};

struct Test {
    Sequence sequences[5];
    int numSequences;
};

// Test variables
bool isTestRunning = false;
Test currentTest;
int currentSequenceIndex = 0;
unsigned long sequenceStartTime = 0;
float currentTargetTemp = 0;
unsigned long currentDuration = 0;

// JSON Buffer for parsing
char incomingString[1024];
StaticJsonDocument<2048> jsonBuffer;

// Define Variables
double temperatureRoom;
double temperatureDesired = -41;  // Invalid value to start the chamber in RESET state
float TemperatureThreshold = 0;
// double temperatureRoomOld;
// double temperatureDesiredOld;
int longheatingflag = 0;

// function for checking how much memory remains after parsing JSON of different sizes
extern "C" {
    char* sbrk(int incr);
}
int freeMemory() {
    char top;
    return &top - sbrk(0);
}


void setup() {
    // Initialise Serial
    Serial.begin(9600);

    // Initialise thermocouples
    sensors1.begin();
    sensors2.begin();

    // Initialise LCD
    lcd.init();
    temperatureRoom = getTemperature();
    currentTest.numSequences = 0;
}

float getTemperature() {
    float roomTemperature = 0;
    sensors1.setWaitForConversion(false);
    sensors2.setWaitForConversion(false);
    sensors1.requestTemperatures();
    sensors2.requestTemperatures();
    // get average room_temperature
    roomTemperature = (sensors1.getTempCByIndex(0) + sensors2.getTempCByIndex(0)) / 2;
    return roomTemperature;
}

// void showData() {
//     displayLCD(temperatureRoom, temperatureDesired);
//     displaySerial();
//     if(abs(temperatureRoomOld - temperatureRoom) > 0.1 || 
//             (temperatureDesiredOld - temperatureDesired)!= 0 || 
//             stateHeaterOld != stateHeater || stateCoolerOld != stateCooler) {
//         dataEvent = true;; // if the temp gradient is more than 0.1 deg
//     } else {
//         dataEvent = false;
//     }
//     if (dataEvent) {
//         displaySerial();
//     }
// }

void displayLCD(float tempRoom, int tempDesired) {
    lcd.backlight();  // turn off backlight
    lcd.display();

    lcd.setCursor(0, 0);
    lcd.print("Room: ");
    lcd.print(tempRoom);
    lcd.print(" C");

    //// Attempt at showing test updates on LCD, but LCD too smol
    // if (isTestRunning) {
    //     unsigned long elapsedTime = (millis() - sequenceStartTime) / 60000;
    //     unsigned long remainingTime = (currentDuration / 60000) - elapsedTime;
    //     lcd.setCursor(13, 0);
    //     lcd.print(remainingTime);
    //     lcd.print("m");
    //     lcd.setCursor(0, 1);  // 2nd argument represent the number of the line we're writing on
    //     lcd.print("Goal:");
    //     lcd.print(tempDesired);
    //     lcd.print("C");
    //     float percentComplete = (float)(millis() - sequenceStartTime) / currentDuration * 100;
    //     if (percentComplete > 100) percentComplete = 100;
    //     lcd.setCursor(12, 1);
    //     lcd.print((int)percentComplete);
    //     lcd.print("%");
    // } else if (currentSequenceIndex >= currentTest.numSequences && currentTest.numSequences != 0) {
    //     lcd.setCursor(0, 1);  // 2nd argument represent the number of the line we're writing on
    //     lcd.print("Test complete");
    // } else {
    // }

    lcd.setCursor(0, 1);
    lcd.print("Goal: ");
    if (tempDesired == -41) {
        lcd.print("-");
    } else {
        lcd.print(tempDesired);
        lcd.print(" C");
    }
}

void displaySerial() {
    Serial.print(F("Room_temp: "));
    Serial.print(temperatureRoom);
    Serial.print(F(" | Desired_temp: "));
    if (temperatureDesired == -41) {
        Serial.print("-");
    } else {
        Serial.print(temperatureDesired);
    }
    Serial.print(F(" | Heater: "));
    Serial.print(stateHeater);
    Serial.print(F(" | Cooler: "));
    Serial.print(stateCooler);
    Serial.print(F(" | LH Indicator: "));
    Serial.println(longheatingflag);
}

void displayLCDOff() {
    lcd.noBacklight();
    lcd.noDisplay();
}

bool isTemperatureReached(float targetTemp, float currentTemp) {
    return abs(targetTemp - currentTemp) <= 0.1;
}

bool holdForPeriod(unsigned long duration) {
    Serial.print("Checking timer: ");
    Serial.print(millis() - sequenceStartTime);
    Serial.print(" / ");
    Serial.println(duration);
    return millis() - sequenceStartTime >= duration;
}

void PWMHeater(int dutyCycle, unsigned long PeriodHeater) {
    unsigned long elapsedTime = millis() - timerHeater;
    if (elapsedTime > (dutyCycle * PeriodHeater) / 100) {
        heater.off();
    } else {
        cooler.off();
        heater.on();
    }
    if (elapsedTime > PeriodHeater) {
        timerHeater = millis();
    }
}

// dutyCycle has to be 0..100

void PWMCooler(int dutyCycle, unsigned long PeriodCooler) {
    unsigned long elapsedTime = millis() - timerCooler;
    if (elapsedTime > (dutyCycle * PeriodCooler) / 100) {
        cooler.off();
    } else {
        heater.off();
        cooler.on();
    }
    if (elapsedTime > PeriodCooler) { 
        timerCooler = millis();
    }
}

void parseTextFromJson(JsonDocument& doc) {
<<<<<<< HEAD
=======
    JsonObject test = doc["test_1"];
    if (!test.containsKey("chamber_sequences")) {
        Serial.println("Error: Missing 'chamber_sequences' in test data");
        return;
    }

    // For future display of test info on LCD
    // if (test.containsKey("sketch")) {
    //     const char* sketch = test["sketch"];
    //     Serial.print("Sketch to upload: ");
    //     Serial.println(sketch);
    // }
    // if (test.containsKey("expected output")) {
    //     const char* expected_output = test["expected_output"];
    //     Serial.print("Expected output: ");
    //     Serial.println(expected_output);
    // }
    

>>>>>>> cli-integration
    JsonArray sequences = doc.as<JsonArray>();
    int numSequences = sequences.size();
    if (numSequences > 5) numSequences = 5;         // how many?

    currentTest.numSequences = numSequences;

    for (int i = 0; i < numSequences; i++) {
        JsonObject sequence = sequences[i];

        if (!sequence.containsKey("temp") || !sequence.containsKey("duration")) {
            Serial.println("Error: Missing 'temp' or 'duration' in JSON sequence");
            continue;   // skip this sequence if the keys are missing
        }
        currentTest.sequences[i].targetTemp = sequence["temp"].as<float>();
        currentTest.sequences[i].duration = sequence["duration"].as<unsigned long>();
    }
    jsonBuffer.clear();

    // start the test with the first sequence
    currentSequenceIndex = 0;
    isTestRunning = true;

    // Ensure desired temperature is set and transition to the appropriate state
    setTemperature(currentTest.sequences[0].targetTemp);
    status =  REPORT;
}

bool printedWaiting = false;
bool printedRunning = false;

void runCurrentSequence() {
    if (currentSequenceIndex >= currentTest.numSequences) {
        Serial.println("Test complete");
        isTestRunning = false;
        printedWaiting = false;
        printedRunning = false;
        status = REPORT;
        return;
    }

    Sequence currentSequence = currentTest.sequences[currentSequenceIndex];
    float targetTemp = currentSequence.targetTemp;
    unsigned long duration = currentSequence.duration;

    // store current duration for the SHOW RUNNING SEQUENCE command
    currentDuration = duration;

    if (!printedRunning) {
        Serial.print("Running sequence: Target temp = ");
        Serial.print(targetTemp);
        Serial.print(" Duration = ");
        Serial.println(duration);
        printedRunning = true;
    }

    // check if target temp is reached
    if (!isTemperatureReached(targetTemp, temperatureRoom)) {
        if (!printedWaiting) {
            Serial.println("Waiting for target temp to be reached");
            printedWaiting = true;
        }
        return;
    }
    if (sequenceStartTime == 0) {
        sequenceStartTime = millis();
        Serial.println("Target temp reached! Starting timer.");
    }

    if (holdForPeriod(duration)) {
        Serial.println("Sequence complete");
        currentSequenceIndex++;
        sequenceStartTime = 0;

        if (currentSequenceIndex < currentTest.numSequences) {
            setTemperature(currentTest.sequences[currentSequenceIndex].targetTemp);
        }
    }
}

void changeTemperature() {
    if (buttonIncrease.read()== HIGH && buttonDecrease.read()== LOW) temperatureDesired += 5;
    if (buttonDecrease.read()== HIGH && buttonIncrease.read()== LOW) temperatureDesired -= 5;

    if (temperatureDesired >= TEMPERATURE_MAX) temperatureDesired = TEMPERATURE_MAX;
    if (temperatureDesired == -41) { handleResetState(); }
    else if (temperatureDesired <= TEMPERATURE_MIN) temperatureDesired = TEMPERATURE_MIN;
}

void displayStatus() {
    Serial.print("status: ");
    Serial.println(status);
}

enum TestState { IDLE, RUNNING_TEST };
TestState currentTestState = IDLE;
unsigned long startTime = 0;    // Timing variable for test steps

void setTemperature(float temp) {
    if (temp >= TEMPERATURE_MAX) {
        temperatureDesired = TEMPERATURE_MAX;
        Serial.println("Specified temperature exceeds maximum allowed temperature\n");
<<<<<<< HEAD
        Serial.println("Setting temperature to " + String(TEMPERATURE_MAX) + "¬∞C");
    } else if (temp <= TEMPERATURE_MIN) {
        temperatureDesired = TEMPERATURE_MIN;
        Serial.println("Specified temperature is lower than the minimum allowed temperature\n");
        Serial.println("Setting temperature to " + String(TEMPERATURE_MIN) + "¬∞C");
    } else {
        temperatureDesired = temp;
        Serial.println("Setting temperature to " + String(temp) + "¬∞C");
=======
        Serial.println("Setting temperature to " + String(TEMPERATURE_MAX) + "¬¨‚àûC");
    } else if (temp <= TEMPERATURE_MIN) {
        temperatureDesired = TEMPERATURE_MIN;
        Serial.println("Specified temperature is lower than the minimum allowed temperature\n");
        Serial.println("Setting temperature to " + String(TEMPERATURE_MIN) + "¬¨‚àûC");
    } else {
        temperatureDesired = temp;
        Serial.println("Setting temperature to " + String(temp) + "¬¨‚àûC");
>>>>>>> cli-integration
        Serial.print("Temperature desired set to: ");
        Serial.println(temp);  // Debug to confirm the desired temp is set
    }
}

void parseCommand(String command) {
    if (command.startsWith("SET TEMP ")) {
        temperatureDesired = command.substring(9).toFloat();
        Serial.println("Temp set to: " + String(temperatureDesired));
        displaySerial();
    }
    else if (command == "SYSTEM OFF") {
        status = EMERGENCY_STOP;
        Serial.println("SYSTEM OFF/EMERGENCY_STOP");
    }
    else if (command == "RESET") {
        status = RESET;
        Serial.println("RESET");
    }
    else if (command == "REPORT") {
        status = REPORT;
        Serial.println("System Report:");
        displaySerial();
    }
    else if (command == "SHOW DATA") {
        displaySerial();
    }
    else if (command == "SHOW RUNNING SEQUENCE") {
        if (isTestRunning) {
            //Serial.println("Processing SHOW RUNNING SEQUENCE...");
            Serial.print("Running sequence: Target temp = ");
            Serial.print(temperatureDesired, 2);
            Serial.print(" Duration = ");
            Serial.println(currentDuration);
        } else {
            Serial.println("No sequence is currently running.");
        }
    }
    //displayStatus();
}

void handleResetState() {
    if (switchSystem.read() == LOW) {
        displayLCD(temperatureRoom, temperatureDesired);
        readAndParseSerial();
    } else {
        displayLCDOff();
    }

    if (switchSystem.read() == HIGH) {
        status = EMERGENCY_STOP; // shut everything down
    } else if (switchStart.pressed() || switchStart.held()) {
        status = REPORT; // check temperature and report result
    }
    changeTemperature();

    heater.off();
    cooler.off();
    stateHeater = 0;
    stateCooler = 0;
    longheatingflag = 0;
}

void handleHeatingState() {
    if (switchSystem.read() == HIGH || switchStart.read() == HIGH) {
        status = RESET;
        return;
    }
    cooler.off();

    if (switchSystem.released()) {
        status = EMERGENCY_STOP;
    }
    if (switchSystem.read() == LOW && switchStart.released()) {
        status = RESET; // go to reset if startswitch is off and system is on
    }

    if(TemperatureThreshold > -0.1) {
        status = REPORT;
        longheatingflag = 0;
    } else if(TemperatureThreshold < -4 && TemperatureThreshold > -8) {
        dutyCycleHeater = 100;
        PeriodHeater = 60000;
        longheatingflag = 1;
    } else if(TemperatureThreshold < -8) {
        dutyCycleHeater = 100; PeriodHeater = 120000; longheatingflag = 1; // turn heater on for 2 mins
    } else if(TemperatureThreshold > -4 && longheatingflag == 0) {
        dutyCycleHeater = 80; PeriodHeater = 25000; //on for 20 seconds and off for 5
    } else if(TemperatureThreshold > -4 && longheatingflag == 1) {
        dutyCycleHeater = 0;  
    }

    PWMHeater(dutyCycleHeater, PeriodHeater);
    stateCooler = 0;
    stateHeater = 1;

    // Serial.println("DutyCycleHeater: " + String(dutyCycleHeater));
    // Serial.println("PeriodHeater: " + String(PeriodHeater));

}

void handleCoolingState() {
    if (switchSystem.read() == HIGH || switchStart.read() == HIGH) {
        status = RESET;
        return;
    }

    heater.off();
<<<<<<< HEAD
=======

    if (switchSystem.released()) {
        status = EMERGENCY_STOP;
    }
    if (switchSystem.read() == LOW && switchStart.released()) {
        status = RESET;
    }

    if(TemperatureThreshold < 0.4) {
        status = REPORT;
    } else if(TemperatureThreshold > 1) {
        dutyCycleCooler = 100;
        PeriodCooler=2000;
    } else if(TemperatureThreshold < 1 && TemperatureThreshold > 0.4) {
        dutyCycleCooler = 29;
        PeriodCooler=7000; // on for 2 seconds and off for 5
    } 
    longheatingflag = 0;

    PWMCooler(dutyCycleCooler, PeriodCooler);
    stateHeater = 0;
    stateCooler = 1;

    // Serial.println("DutyCycleCooler: " + String(dutyCycleCooler));
    // Serial.println("PeriodCooler: " + String(PeriodCooler));
}

void handleReportState() {
    if (switchSystem.read() == HIGH) {
        status = EMERGENCY_STOP;
    } else if (switchStart.released()) {
        status = RESET;
    } else if (switchStart.read() == LOW) {
        if(TemperatureThreshold > 0.4) {
            status = COOLING;
        } else if(TemperatureThreshold < -0.1) {
            status = HEATING;
        }
    }
}

void handleEmergencyStopState() {
    heater.off();
    cooler.off();
    stateHeater = 0;
    stateCooler = 0;
    displayLCDOff();
    longheatingflag =0;
    if (switchSystem.held()) {
        status = RESET;
    }
}

void readAndParseSerial() {
    if (switchSystem.read() == LOW) {
        if (Serial.available() > 0) {
            // Read the incoming data in chunks instead of one character at a time
            int len = Serial.readBytesUntil('\n', incomingString, sizeof(incomingString) - 1);
            incomingString[len] = '\0'; // null-terminate the string

            // Serial.print("Received string: ");
            // Serial.println(incomingString);

            DeserializationError error = deserializeJson(jsonBuffer, incomingString);
            // Handle the input string (either a command or JSON)
            if (!error) {
                parseTextFromJson(jsonBuffer);  // Parse the JSON
            } else {
                parseCommand(incomingString);  // Parse regular commands
            }

            incomingString[0] = '\0';
        }
    } else {
        //Serial.println("Switches are OFF. Test will not be processed.");
    }
}

unsigned long lastUpdate = 0;
unsigned long updateInterval = 500;

bool printedLCDOff = false;

void loop() {  

    unsigned long currentMillis = millis();
    if (switchSystem.read() == LOW) {
        displayLCD(temperatureRoom, temperatureDesired);
        //displaySerial();
        if (currentMillis - lastUpdate >= updateInterval) {
            lastUpdate = currentMillis;
        }
    } else {
        displayLCDOff();
        //Serial.println("LCD turning off");
    }

    // Used in showData()
    // temperatureRoomOld = temperatureRoom;
    // stateHeaterOld = stateHeater;
    // stateCoolerOld = stateCooler;
    // temperatureDesiredOld = temperatureDesired;

    // get latest room temp
    temperatureRoom = getTemperature();
    TemperatureThreshold = temperatureRoom - temperatureDesired;

    // Check if data is available on the serial port
    readAndParseSerial();

    if (isTestRunning) {
        runCurrentSequence();
    }

    switch (status) {
        case RESET:
            handleResetState();
            break;
        case HEATING:
            handleHeatingState();
            break;
        case COOLING:
            handleCoolingState();
            break;
        case REPORT:
            handleReportState();
            break;
        case EMERGENCY_STOP:
            handleEmergencyStopState();
            break;
    }
}
>>>>>>> cli-integration

    if (switchSystem.released()) {
        status = EMERGENCY_STOP;
    }
    if (switchSystem.read() == LOW && switchStart.released()) {
        status = RESET;
    }

    if(TemperatureThreshold < 0.4) {
        status = REPORT;
    } else if(TemperatureThreshold > 1) {
        dutyCycleCooler = 100;
        PeriodCooler=2000;
    } else if(TemperatureThreshold < 1 && TemperatureThreshold > 0.4) {
        dutyCycleCooler = 29;
        PeriodCooler=7000; // on for 2 seconds and off for 5
    } 
    longheatingflag = 0;

    PWMCooler(dutyCycleCooler, PeriodCooler);
    stateHeater = 0;
    stateCooler = 1;

    // Serial.println("DutyCycleCooler: " + String(dutyCycleCooler));
    // Serial.println("PeriodCooler: " + String(PeriodCooler));
}

void handleReportState() {
    if (switchSystem.read() == HIGH) {
        status = EMERGENCY_STOP;
    } else if (switchStart.released()) {
        status = RESET;
    } else if (switchStart.read() == LOW) {
        if(TemperatureThreshold > 0.4) {
            status = COOLING;
        } else if(TemperatureThreshold < -0.1) {
            status = HEATING;
        }
    }
}

void handleEmergencyStopState() {
    heater.off();
    cooler.off();
    stateHeater = 0;
    stateCooler = 0;
    displayLCDOff();
    longheatingflag =0;
    if (switchSystem.held()) {
        status = RESET;
    }
}

void readAndParseSerial() {
    if (switchSystem.read() == LOW) {
        if (Serial.available() > 0) {
            // Read the incoming data in chunks instead of one character at a time
            int len = Serial.readBytesUntil('\n', incomingString, sizeof(incomingString) - 1);
            incomingString[len] = '\0'; // null-terminate the string

            // Serial.print("Received string: ");
            // Serial.println(incomingString);

            DeserializationError error = deserializeJson(jsonBuffer, incomingString);
            // Handle the input string (either a command or JSON)
            if (!error) {
                parseTextFromJson(jsonBuffer);  // Parse the JSON
            } else {
                parseCommand(incomingString);  // Parse regular commands
            }

            incomingString[0] = '\0';
        }
    } else {
        //Serial.println("Switches are OFF. Test will not be processed.");
    }
}

unsigned long lastUpdate = 0;
unsigned long updateInterval = 500;

bool printedLCDOff = false;

void loop() {  

    unsigned long currentMillis = millis();
    if (switchSystem.read() == LOW) {
        displayLCD(temperatureRoom, temperatureDesired);
        //displaySerial();
        if (currentMillis - lastUpdate >= updateInterval) {
            lastUpdate = currentMillis;
        }
    } else {
        displayLCDOff();
        //Serial.println("LCD turning off");
    }

    // Used in showData()
    // temperatureRoomOld = temperatureRoom;
    // stateHeaterOld = stateHeater;
    // stateCoolerOld = stateCooler;
    // temperatureDesiredOld = temperatureDesired;

    // get latest room temp
    temperatureRoom = getTemperature();
    TemperatureThreshold = temperatureRoom - temperatureDesired;

    // Check if data is available on the serial port
    readAndParseSerial();

    if (isTestRunning) {
        runCurrentSequence();
    }

    switch (status) {
        case RESET:
            handleResetState();
            break;
        case HEATING:
            handleHeatingState();
            break;
        case COOLING:
            handleCoolingState();
            break;
        case REPORT:
            handleReportState();
            break;
        case EMERGENCY_STOP:
            handleEmergencyStopState();
            break;
    }
}
