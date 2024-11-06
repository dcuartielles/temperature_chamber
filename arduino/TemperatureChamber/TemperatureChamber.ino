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
#include <ArduinoJson.h>
#include <RTC.h>

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
unsigned long periodHeater = 0;
unsigned long periodCooler = 0;

// State machine variables
int stateHeaterOld = 0;
int stateCoolerOld = 0;
int dutyCycleHeater = 0;
int dutyCycleCooler = 0;
int status = EMERGENCY_STOP;
bool dataEvent = false;

// global variables to store switch states and flags
bool systemSwitchState = false;
bool startSwitchState = false;
bool stopSwitchState = false;

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
unsigned long currentDuration = 0;

const int MAX_QUEUED_TESTS = 5;

// queue for tests
Test testQueue[MAX_QUEUED_TESTS];
String testNames[MAX_QUEUED_TESTS];
int queuedTestCount = 0;
int currentTestIndex = 0;

// track current test and sequence
String currentTestName = "";

// JSON Buffer for parsing
char incomingString[1024];
StaticJsonDocument<2048> jsonBuffer;

// Define Variables
float temperatureThreshold = 0;

// struct for state of the heating/cooling system
struct ChamberState {
    bool isHeating;
    bool isCooling;
    float temperatureRoom;
    int temperatureDesired;
    int longHeatingFlag;
    unsigned long lastHeaterOnTime;
    unsigned long lastCoolerOnTime;
};

ChamberState chamberState;

String lastShutdownCause = "Unknown";
String lastHeatingTime = "";

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

    // Initialize RTC
    if (!RTC.begin()) {
        Serial.println("RTC initialization failed!");
    }

    if (!RTC.isRunning()) {
        RTCTime defaultTime(2024, Month::NOVEMBER, 1, 10, 26, 0, DayOfWeek::FRIDAY, SaveLight::SAVING_TIME_INACTIVE);
        RTC.setTimeIfNotRunning(defaultTime);
    }

    // Initialise thermocouples
    sensors1.begin();
    sensors2.begin();

    // Initialise LCD
    lcd.init();
    chamberState.temperatureRoom = getTemperature();
    chamberState.temperatureDesired = -41;
    chamberState.longHeatingFlag = 0;
    chamberState.isHeating = false;
    chamberState.isCooling = false;
    chamberState.lastHeaterOnTime = millis();
    chamberState.lastCoolerOnTime = millis();

    currentTest.numSequences = 0;

    readAndParseSerial();
}

String getCurrentTimestamp() {
    RTCTime now;
    if (RTC.getTime(now)) {
        return now.toString();
    } else {
        return "Error: Unable to get time";
    }
}

String getLastHeatingTime() {
    return lastHeatingTime.isEmpty() ? "N/A" : lastHeatingTime;
}

void setInitialTimestamp(JsonObject& commandParams) {
    if (commandParams.containsKey("timestamp")) {
        String timestamp = commandParams["timestamp"].as<String>();
        int year, month, day, hour, minute, second;
        sscanf(timestamp.c_str(), "%4d-%2d-%2dT%2d:%2d:%2d", &year, &month, &day, &hour, &minute, &second);

        RTCTime initialTime(day, static_cast<Month>(month - 1), year, hour, minute, second, DayOfWeek::SUNDAY, SaveLight::SAVING_TIME_INACTIVE);
        if (RTC.setTime(initialTime)) {
            Serial.println("RTC updated with initial timestamp from python app.");
        } else {
            Serial.println("Error setting RTC time.");
        }
    } else {
        Serial.println("Timestamp key not found in commandParams.");
    }
}

void sendHandshake() {
    StaticJsonDocument<512> handshakeDoc;

    handshakeDoc["handshake"]["timestamp"] = getCurrentTimestamp();
    handshakeDoc["handshake"]["machine_state"] = getMachineState();
    handshakeDoc["handshake"]["last_shutdown_cause"] = lastShutdownCause;
    handshakeDoc["handshake"]["last_heat_time"] = getLastHeatingTime();

    serializeJson(handshakeDoc, Serial);
    Serial.println();
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

void displayLCD(float tempRoom, int tempDesired) {
    lcd.backlight();  // turn off backlight
    lcd.display();

    lcd.setCursor(0, 0);
    lcd.print("Room: ");
    lcd.print(tempRoom);
    lcd.print(" C");
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
    Serial.print(chamberState.temperatureRoom);
    Serial.print(F(" | Desired_temp: "));
    if (chamberState.temperatureDesired == -41) {
        Serial.print("-");
    } else {
        Serial.print(chamberState.temperatureDesired);
    }
    Serial.print(F(" | Heater: "));
    Serial.print(chamberState.isHeating ? 1 : 0);
    Serial.print(F(" | Cooler: "));
    Serial.print(chamberState.isCooling ? 1 : 0);
    Serial.print(F(" | LH Indicator: "));
    Serial.println(chamberState.longHeatingFlag);
}

void displayLCDOff() {
    lcd.noBacklight();
    lcd.noDisplay();
}

bool isTemperatureReached(float targetTemp, float currentTemp) {
    return currentTemp >= targetTemp - 0.1;
}

bool holdForPeriod(unsigned long duration) {
    // Serial.print("Checking timer: ");
    // Serial.print(millis() - sequenceStartTime);
    // Serial.print(" / ");
    // Serial.println(duration);
    return millis() - sequenceStartTime >= duration;
}

int getTimeLeft(unsigned long duration, Sequence currentSequence) {
    if (isTestRunning && isTemperatureReached(currentSequence.targetTemp, chamberState.temperatureRoom)) {
        int timeLeft = (duration - (millis() - sequenceStartTime)) / 1000;
        return timeLeft;
    } else {
        return 0;
    }
}

// dutyCycle has to be 0..100
void controlRelay(Led& relay, int dutyCycle, unsigned long period, unsigned long& lastOnTimer) {
    unsigned long elapsedTime = millis() - lastOnTimer;
    if (elapsedTime > (dutyCycle * period) / 100) {
        relay.off();
    } else {
        relay.on();
    }
    if (elapsedTime > period) {
        lastOnTimer = millis();
    }
}

void queueTest(const Test& test, const String& testName) {
    if (queuedTestCount < MAX_QUEUED_TESTS) {
        testQueue[queuedTestCount] = test;
        testNames[queuedTestCount] = testName;
        queuedTestCount++;
        Serial.print("Queued test: ");
        Serial.println(testName);
    } else {
        Serial.println("Test queue is full. Cannot add more tests.");
    }
}

// parse tests and add to queue by name
void parseAndQueueTests(JsonObject& tests) {
    for (JsonPair testPair : tests) {
        JsonObject testJson = testPair.value().as<JsonObject>();
        Test newTest;
        String testName = testPair.key().c_str();

        // check for required fields
        if (!testJson.containsKey("chamber_sequences")) {
            Serial.println("Error: Missing 'chamber_sequences' in test data");
            continue;
        }

        JsonArray sequences = testJson["chamber_sequences"];
        newTest.numSequences = sequences.size();
        if (newTest.numSequences > 5) {
            newTest.numSequences = 5;         // how many?
        }

        // iterate through each sequence in the chamber_sequences array
        for (int i = 0; i < newTest.numSequences; i++) {
            JsonObject sequence = sequences[i];

            if (!sequence.containsKey("temp") || !sequence.containsKey("duration")) {
                Serial.println("Error: Missing 'temp' or 'duration' in JSON sequence");
                continue;
            }
            newTest.sequences[i].targetTemp = sequence["temp"].as<float>();
            newTest.sequences[i].duration = sequence["duration"].as<unsigned long>();
        }

        queueTest(newTest, testName);
    }

    jsonBuffer.clear();

    runNextTest();
}

void runNextTest() {
    if (currentTestIndex < queuedTestCount) {
        currentTest = testQueue[currentTestIndex];
        isTestRunning = true;
        currentSequenceIndex = 0;
        currentTestName = testNames[currentTestIndex];
        setTemperature(currentTest.sequences[currentSequenceIndex].targetTemp);
        status = REPORT;
        Serial.print("Running test: ");
        Serial.println(currentTestName);
    }
}

void parseAndRunManualSet(JsonObject& commandParams) {

        float temp = commandParams["temp"];
        unsigned long duration = commandParams["duration"];
        setTemperature(temp);
        Serial.print("Manual temp set to ");
        Serial.println(temp);
        Serial.print("Duration: ");
        Serial.println(duration);

        jsonBuffer.clear();
}

void parseAndRunCommands(JsonObject& commands) {
    for (JsonPair commandPair : commands) {
        String command = commandPair.key().c_str();
        JsonObject commandParams = commandPair.value().as<JsonObject>();

        if (command == "PING") {
            sendPingResponse();
        } 
        if (systemSwitchState) {
            if (command == "INTERRUPT_TEST") {

            } else if (command == "SHOW_DATA") {
                displaySerial();
            } else if (command == "SET_TEMP") {
                parseAndRunManualSet(commandParams);
            } else if (command == "RESET") {
                status = RESET;
                Serial.println("System reset via command.");
            } else if (command == "EMERGENCY_STOP") {
                status = EMERGENCY_STOP;
                sendPingResponse();
                Serial.println("Emergency Stop initiated via command.");
            } else if (command == "SHOW_RUNNING_SEQUENCE") {
                if (isTestRunning) {
                    Serial.print("Running sequence: Target temp = ");
                    Serial.print(chamberState.temperatureDesired);
                    Serial.print("°C Duration = ");
                    Serial.print(currentDuration / 60000);
                    Serial.println(" minutes");

                } else {
                    Serial.println("No sequence is currently running.");
                }
            } else {
                Serial.print("Error: Unknown command '");
                Serial.print(command);
                Serial.println("'.");
            }
        } else {
            Serial.println("System switch is off, please switch it on.");
        }
    }
}

void sendPingResponse() {
    StaticJsonDocument<512> responseDoc;

    Sequence currentSequence = currentTest.sequences[currentSequenceIndex];

    responseDoc["ping_response"]["alive"] = true;
    responseDoc["ping_response"]["timestamp"] = getCurrentTimestamp();
    responseDoc["ping_response"]["machine_state"] = getMachineState();
    responseDoc["ping_response"]["current_temp"] = chamberState.temperatureRoom;

    JsonObject testStatus = responseDoc["ping_response"].createNestedObject("test_status");
    testStatus["is_test_running"] = isTestRunning;
    testStatus["current_test"] = currentTestName;
    testStatus["current_sequence"] = currentSequenceIndex + 1;
    testStatus["desired_temp"] = chamberState.temperatureDesired;
    testStatus["current_duration"] = currentDuration;
    testStatus["time_left"] = getTimeLeft(currentDuration, currentSequence);

    serializeJson(responseDoc, Serial);
    Serial.println();
}

String getMachineState() {
    switch (status) {
        case RESET:
            return "RESET";
        case HEATING:
            return "HEATING";
        case COOLING:
            return "COOLING";
        case REPORT:
            return "REPORT";
        case EMERGENCY_STOP:
            return "EMERGENCY_STOP";
        default:
            return "UNKNOWN";
    
    }
}

void parseTextFromJson(JsonDocument& doc) {
    if (doc.containsKey("handshake")) {
        JsonObject handshake = doc["handshake"];
        setInitialTimestamp(handshake);
        sendHandshake();
    } else if (doc.containsKey("tests") && systemSwitchState) {             // if json consists of tests
        JsonObject test = doc["tests"];
        parseAndQueueTests(test);
    } else if (doc.containsKey("commands")) {   // if json consists of commands
        JsonObject commands = doc["commands"];
        parseAndRunCommands(commands);
    } else {
        Serial.println("Error: Invalid JSON format");
    }
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
        Serial.print("°C Duration = ");
        Serial.println(String(duration / 60000) + " minutes");
        printedRunning = true;
    }

    // check if target temp is reached
    if (!isTemperatureReached(targetTemp, chamberState.temperatureRoom)) {
        if (!printedWaiting) {
            Serial.println("Waiting for target temp to be reached");
            printedWaiting = true;
        }
        return;
    }
    if (sequenceStartTime == 0) {
        sequenceStartTime = millis();
        Serial.println("Target temperature reached! Starting timer.");
    }

    if (holdForPeriod(duration)) {
        Serial.println("Sequence complete");
        currentSequenceIndex++;
        sequenceStartTime = 0;
        printedWaiting = false;
        printedRunning = false;

        if (currentSequenceIndex < currentTest.numSequences) {
            setTemperature(currentTest.sequences[currentSequenceIndex].targetTemp);
        }
    }
}

void changeTemperature() {
    if (buttonIncrease.read()== HIGH && buttonDecrease.read()== LOW) chamberState.temperatureDesired += 5;
    if (buttonDecrease.read()== HIGH && buttonIncrease.read()== LOW) chamberState.temperatureDesired -= 5;

    if (chamberState.temperatureDesired >= TEMPERATURE_MAX) {
        chamberState.temperatureDesired = TEMPERATURE_MAX;
    }
    // if (chamberState.temperatureDesired == -41) { handleResetState(); }
    else if (chamberState.temperatureDesired <= TEMPERATURE_MIN && chamberState.temperatureDesired != -41)  {
        chamberState.temperatureDesired = TEMPERATURE_MIN;
    }
}

void setTemperature(float temp) {
    if (temp >= TEMPERATURE_MAX) {
        chamberState.temperatureDesired = TEMPERATURE_MAX;
        Serial.println("Specified temperature exceeds maximum allowed temperature\n");
    } else if (temp <= TEMPERATURE_MIN) {
        chamberState.temperatureDesired = TEMPERATURE_MIN;
        Serial.println("Specified temperature is lower than the minimum allowed temperature\n");
        Serial.println("Setting temperature to " + String(TEMPERATURE_MIN) + "°");
    } else {
        chamberState.temperatureDesired = temp;
        Serial.print("Setting temperature to ");
        Serial.print(temp);
        Serial.println("°");
    }
}

int getSwitchStatus() {
    int switchStatus;
    if (switchSystem.read() == LOW) {
        switchStatus += 10;
    }
    if (switchStart.read() == LOW) {
        switchStatus += 1;
    }
    return switchStatus;
}

// centralized switch handling
void updateSwitchStates() {
    systemSwitchState = switchSystem.read() == LOW;
    startSwitchState = switchStart.read() == LOW;
    stopSwitchState = switchStart.released();  // stop condition from releasing the start switch
}


void handleResetState() {
    displayLCD(chamberState.temperatureRoom, chamberState.temperatureDesired);

    if (!systemSwitchState) {
        status = EMERGENCY_STOP;
        return;
    }
    if (startSwitchState) {
        status = REPORT;
    }
    // allow manual control of temperature from buttons
    changeTemperature();

    // turn off all outputs
    heater.off();
    cooler.off();
    chamberState.isHeating = false;
    chamberState.isCooling = false;
    chamberState.longHeatingFlag = 0;

}

void handleHeatingState() {
    if (!systemSwitchState || stopSwitchState) {
        status = RESET;
        return;
    }
    cooler.off();

    if(temperatureThreshold > -0.1) {

        // Serial.println("\ncond: threshold > -0.1");
        // Serial.println("Actual:");
        // Serial.println("Threshold: " + String(temperatureThreshold));
        // Serial.println("Going to report\n");

        chamberState.longHeatingFlag = 0;
        chamberState.isHeating = false;

        lastHeatingTime = getCurrentTimestamp();    // capture current timestamp for handshake

        status = REPORT;
        return;
    } else if(temperatureThreshold < -4) {
        dutyCycleHeater = 100;
        periodHeater = (temperatureThreshold < -8) ? 120000 : 60000;
        chamberState.longHeatingFlag = 1;

        // Serial.println("\ncond: threshold < -4");
        // Serial.println("Actual:");
        // Serial.println("Threshold: " + String(temperatureThreshold));
        // Serial.println("Setting dutycycle to 100");
        // Serial.println("Dutycycle: " + String(dutyCycleHeater));
        // Serial.println("Setting periodHeater to 120000 if threshold < -8, otherwise 60000");
        // Serial.println("PeriodHeater: " + String(periodHeater));
        // Serial.println("Setting lh flag to 1");
        // Serial.println("lh flag: " + String(chamberState.longHeatingFlag));
        // Serial.println();

    } else if(temperatureThreshold > -4) {
        dutyCycleHeater = (chamberState.longHeatingFlag) ? 0 : 80;
        periodHeater = 25000; //on for 20 seconds and off for 5

        // Serial.println("\ncond: threshold > -4");
        // Serial.println("Actual:");
        // Serial.println("Threshold: " + String(temperatureThreshold));
        // Serial.println("Setting dutycycle to 80");
        // Serial.println("Dutycycle: " + String(dutyCycleHeater));
        // Serial.println("Setting periodHeater to 25000");
        // Serial.println("PeriodHeater: " + String(periodHeater));
        // Serial.println();

    }

    controlRelay(heater, dutyCycleHeater, periodHeater, chamberState.lastHeaterOnTime);

    // Serial.println("control relay function values:");
    // Serial.println("Duty cycle: " + String(dutyCycleHeater));
    // Serial.println("Period: " + String(periodHeater));
    // Serial.println("Timer: " + String(chamberState.lastHeaterOnTime));

    chamberState.isHeating = true;

}

void handleCoolingState() {
    if (!systemSwitchState || stopSwitchState) {
        status = RESET;
        return;
    }
    heater.off();

    if(temperatureThreshold < 0.4) {
        chamberState.isCooling = false;
        status = REPORT;
        return;
    } else if(temperatureThreshold > 1) {
        dutyCycleCooler = 100;
        periodCooler=2000;
    } else if(temperatureThreshold < 1) {
        dutyCycleCooler = 29;
        periodCooler=7000; // on for 2 seconds and off for 5
    } 

    controlRelay(cooler, dutyCycleCooler, periodCooler, chamberState.lastCoolerOnTime);
    chamberState.isCooling = true;

}

void handleReportState() {
    if (!systemSwitchState) {
        status = EMERGENCY_STOP;
        return;
    }

    if (stopSwitchState) {
        status = RESET;
        return;
    }

    if(temperatureThreshold > 0.4) {
        status = COOLING;
    } else if(temperatureThreshold < -0.1) {
        status = HEATING;
    }

    readAndParseSerial();
}

void handleEmergencyStopState() {
    heater.off();
    cooler.off();
    chamberState.isHeating = false;
    chamberState.isCooling = false;
    displayLCDOff();
    chamberState.longHeatingFlag = 0;

    if (switchSystem.held()) {
        status = RESET;
    }
}

void runTestSequence() {
    if (isTestRunning) {
        runCurrentSequence();
        if (currentSequenceIndex >= currentTest.numSequences) {
            Serial.print("Test complete: ");
            Serial.println(currentTestName);
            isTestRunning = false;
            currentTestIndex++;
            if (currentTestIndex < queuedTestCount) {
                runNextTest();
            }
        }
    }
}

void readAndParseSerial() {
    if (Serial.available() > 0) {
        // Read the incoming data in chunks instead of one character at a time
        int len = Serial.readBytesUntil('\n', incomingString, sizeof(incomingString) - 1);
        incomingString[len] = '\0'; // null-terminate the string

        DeserializationError error = deserializeJson(jsonBuffer, incomingString);
        // Handle the input string (either a command or JSON)
        if (!error) {
            parseTextFromJson(jsonBuffer);  // Parse the JSON
        }

        incomingString[0] = '\0';
    }
}

unsigned long currentMillis = 0;
unsigned long lastUpdate = 0;
unsigned long updateInterval = 500;

void loop() {  
    currentMillis = millis();

    // Update switch states and temperature readings
    updateSwitchStates();
    chamberState.temperatureRoom = getTemperature();
    if (chamberState.temperatureDesired != -41) {
        temperatureThreshold = chamberState.temperatureRoom - chamberState.temperatureDesired;
    }


    if (systemSwitchState) {
        displayLCD(chamberState.temperatureRoom, chamberState.temperatureDesired);
        //displaySerial();
        if (currentMillis - lastUpdate >= updateInterval) {
            lastUpdate = currentMillis;
        }
    } else {
        displayLCDOff();
        //Serial.println("LCD turning off");
    }

    runTestSequence();
    readAndParseSerial();       // check serial input for new tests or commands

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
        default:
            Serial.println("Invalid state detected!");
    }
}
