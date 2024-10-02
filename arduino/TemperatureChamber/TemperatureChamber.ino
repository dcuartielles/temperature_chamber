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
//#define STANDBY             5

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

bool isTestRunning = false;

//////////////////// OLD //////////////////
int stateHeaterOld = 0;
int stateCoolerOld = 0;
int dutyCycleHeater = 0;
int dutyCycleCooler = 0;
// State machine variables
int status = EMERGENCY_STOP;
bool dataEvent = false;
//////////////////// OLD //////////////////

struct Sequence {
    float targetTemp;
    unsigned long duration;
};

struct Test {
    Sequence sequences[5];
    int numSequences;
};

Test currentTest;
int currentSequenceIndex = 0;
unsigned long sequenceStartTime = 0;
float currentTargetTemp = 0;
unsigned long currentDuration = 0;

// JSON Buffer for parsing
char incomingString[1024];
StaticJsonDocument<2048> jsonBuffer;

// Serial input variables
String inputString = "";
bool receivingJson = false;

// Define Variables
double temperatureRoom;
double temperatureDesired = 70;  // by default, we want to reach max temperature
float TemperatureThreshold = 0;
double temperatureRoomOld;
double temperatureDesiredOld;
int longheatingflag = 0;

void setup() {
    // Initialise Serial
    Serial.begin(9600);

    // Initialise thermocouples
    sensors1.begin();
    sensors2.begin();

    // Initialise LCD
    lcd.init();         // Initialize the LCD screen
    //lcd.backlight();  // Turn on the backlight of lcd
    temperatureRoom = getTemperature();
    showData();
}

float getTemperature() {
    float roomTemperature = 0;
    sensors1.setWaitForConversion(false);
    sensors2.setWaitForConversion(false);
    sensors1.requestTemperatures();
    sensors2.requestTemperatures();
    // get average room_temperature
    roomTemperature = (sensors1.getTempCByIndex(0) + sensors2.getTempCByIndex(0)) / 2;
    //float roomTemperature = (sensors1.getTempCByIndex(0) + sensors2.getTempCByIndex(0)) / 2;
    return roomTemperature;
}

void showData() {
    displayLCD(temperatureRoom, temperatureDesired);
    displaySerial();
    if(abs(temperatureRoomOld - temperatureRoom) > 0.1 || 
            (temperatureDesiredOld - temperatureDesired)!=0 || 
            stateHeaterOld != stateHeater || stateCoolerOld != stateCooler) {
        dataEvent = true;; // if the temp gradient is more than 0.1 deg
    } else {
        dataEvent = false;
    }
    if (dataEvent) {
        displaySerial();
    }
}

void displayLCD(float tempRoom, int tempDesired) {
    lcd.backlight();  // turn off backlight
    lcd.display();
    lcd.setCursor(0, 0);  // 1st argument represent the number of column of the first letter
    lcd.print("Room: ");
    lcd.print(tempRoom);
    lcd.print(" C");

    lcd.setCursor(0, 1);  // 2nd argument represent the number of the line we're writing on
    lcd.print("Goal: ");
    lcd.print(tempDesired);
    lcd.print(" C");
}

void displaySerial() {
    Serial.print(F("Room_temp: "));
    Serial.print(temperatureRoom);
    Serial.print(F(" | Desired_temp: "));
    Serial.print(temperatureDesired);
    Serial.print(F(" | Heater: "));
    Serial.print(stateHeater);
    Serial.print(F(" | Cooler: "));
    Serial.print(stateCooler);
    Serial.print(F(" | LH Indicator: "));
    Serial.println(longheatingflag);  // End with a newline for the next set of data
}

//////////////// OLD ////////////////
void displayLCDOff() {
    lcd.noBacklight();  // turn off backlight
    lcd.noDisplay();
}
//////////////// OLD ////////////////


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
    if (millis() - timerHeater > dutyCycle * PeriodHeater / 100) {
        heater.off();
    } else {
        cooler.off();
        heater.on();
    }
    if (millis() - timerHeater > PeriodHeater) timerHeater = millis();
}

// dutyCycle has to be 0..100

void PWMCooler(int dutyCycle, unsigned long PeriodCooler) {
    if (millis() - timerCooler > dutyCycle * PeriodCooler / 100) {
        cooler.off();
    } else {
        heater.off();
        cooler.on();            // TODO: Test
    }
    if (millis() - timerCooler > PeriodCooler) { 
        timerCooler = millis();
    }
}

void parseTextFromJson(JsonDocument& doc) {

    if (!doc.is<JsonArray>()) {
        Serial.println("Error: Expected JSON array");
        return;
    }

    JsonArray sequences = doc.as<JsonArray>();
    int numSequences = sequences.size();
    if (numSequences > 5) numSequences = 5;

    currentTest.numSequences = numSequences;

    for (int i = 0; i < numSequences; i++) {
        JsonObject sequence = sequences[i];

        if (!sequence.containsKey("temp") || !sequence.containsKey("duration")) {
            Serial.println("Error: Missing 'temp' or 'duration' in JSON sequence");
            continue;   // skip this sequence if the keys are missing
        }

        currentTest.sequences[i].targetTemp = sequence["temp"].as<float>();
        currentTest.sequences[i].duration = sequence["duration"].as<unsigned long>();

        // debug
        Serial.print("Step ");
        Serial.print(i);
        Serial.print(": Target Temp = ");
        Serial.print(currentTest.sequences[i].targetTemp);
        Serial.print(", Duration = ");
        Serial.println(currentTest.sequences[i].duration);
    }

    jsonBuffer.clear();

    // start the test with the first sequence
    currentSequenceIndex = 0;
    isTestRunning = true;
    status = REPORT;
    setTemperature(currentTest.sequences[0].targetTemp);  // <-- This ensures temperatureDesired is set at the start of the test

    Serial.print("Starting test with target temp: ");
    Serial.println(currentTest.sequences[0].targetTemp);
}

void runCurrentSequence() {
    if (currentSequenceIndex >= currentTest.numSequences) {
        // Test finished
        Serial.println("Test complete");
        isTestRunning = false;
        status = REPORT;
        return;
    }

    Sequence currentSequence = currentTest.sequences[currentSequenceIndex];
    float targetTemp = currentSequence.targetTemp;
    unsigned long duration = currentSequence.duration;

    // store current duration for the SHOW RUNNING SEQUENCE command
    currentDuration = duration;

    // debug
    //Serial.print(" Running sequence: Target temp = ");
    //Serial.print(targetTemp);
    //Serial.print(" Duration = ");
    //Serial.println(duration);

    //Serial.print("Status: ");
    //Serial.println(status);

    // check if target temp is reached
    if (!isTemperatureReached(targetTemp, temperatureRoom)) {
        //Serial.println("Waiting for target temp to be reached");
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
//showData();

///////////////////////// OLD /////////////////////////
void changeTemperature() {
    if (buttonIncrease.read()== HIGH && buttonDecrease.read()== LOW) temperatureDesired+=5;
    if (buttonDecrease.read()== HIGH && buttonIncrease.read()== LOW) temperatureDesired-=5;

    // Change Desired temperature by inserting a value in serial input
    if (Serial.available() > 0) 
    {
        inputString = Serial.readStringUntil('\n'); // Read the input as a string until a newline character
        inputString.trim(); // Remove any leading/trailing whitespace

        parseCommand(inputString);
    }  

    if (temperatureDesired >= TEMPERATURE_MAX) temperatureDesired = TEMPERATURE_MAX;
    if (temperatureDesired <= TEMPERATURE_MIN) temperatureDesired = TEMPERATURE_MIN;
}
// dutyCycle has to be 0..100
void displayStatus() {
    Serial.print("status: ");
    Serial.println(status);
}
///////////////////////// OLD /////////////////////////



enum TestState { IDLE, RUNNING_TEST};
TestState currentTestState = IDLE;
unsigned long startTime = 0;    // Timing variable for test steps


// Update status over Serial
void sendStatus(String status) {
    Serial.println(status);
}

void setTemperature(float temp) {
    if (temperatureDesired >= TEMPERATURE_MAX) {
        temperatureDesired = TEMPERATURE_MAX;
        sendStatus("Specified temperature exceeds maximum allowed temperature\n");
        sendStatus("Setting temperature to " + String(TEMPERATURE_MAX) + "¬∞C");
    } else if (temperatureDesired <= TEMPERATURE_MIN) {
        temperatureDesired = TEMPERATURE_MIN;
        sendStatus("Specified temperature is lower than the minimum allowed temperature\n");
        sendStatus("Setting temperature to " + String(TEMPERATURE_MIN) + "¬∞C");
    } else {
        temperatureDesired = temp;
        sendStatus("Setting temperature to " + String(temp) + "¬∞C");
        Serial.print("Temperature desired set to: ");
        Serial.println(temp);  // Debug to confirm the desired temp is set
    }

    Serial.println(temp);  // Debug to confirm the desired temp is set

}

// unclear if working

# define TWOMIN     120000
# define FIVEMIN    300000
# define TENMIN     600000

void parseCommand(String command) {

    // Debug
    Serial.println("Received command: [" + command + "]");

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
    if (command == "SHOW RUNNING SEQUENCE") {
        if (isTestRunning) {
            Serial.println("Processing SHOW RUNNING SEQUENCE...");
            Serial.print("Running sequence: Target temp = ");
            Serial.print(temperatureDesired, 2);
            Serial.print(" Duration = ");
            Serial.println(currentDuration);
        } else {
            Serial.println("No sequence is currently running.");
        }
    }
    displayStatus();
}

void runTestSequence(float temperature, unsigned long duration, String stepDescription) {
    if (!isTestRunning) {
        sendStatus("Starting: " + stepDescription);
        setTemperature(temperature);
        startTime = millis();
        isTestRunning = true;
    }

    if (holdForPeriod(duration)) {
        sendStatus(stepDescription + " complete");
        isTestRunning = false;  // Test step is done, can proceed to the next one
    }
}

void handleResetState() {
    //Serial.println("Entered s1 RESET. actual status = " + String(status));
    if (switchSystem.released() || switchSystem.read() == HIGH) {
        status = EMERGENCY_STOP; // shut everything down
        //Serial.println("s1 reset: Emergency stop activated, status: " + String(status));
    }
    if (switchStart.pressed() || switchStart.held()) {
        status = REPORT; // check temperature and report result
        //Serial.println("s1 reset: report. status : " + String(status));
    }
    changeTemperature();

    // s2
    //Serial.println("Entered s2 RESET. actual status = " + String(status));
    heater.off();
    cooler.off();
    stateHeater = 0;
    stateCooler = 0;
    longheatingflag =0;
    //Serial.println("s2 reset: stateHeater = 0 stateCooler = 0 lh = 0. actual: stateHeater " + String(stateHeater) + " stateCooler = " + String(stateCooler) + " lh = " + String(longheatingflag));
}

void handleHeatingState() {
    //Serial.println("Entered s1 HEATING. actual status = " + String(status));
    cooler.off();
    if (switchSystem.released()) {
        status = EMERGENCY_STOP;
        //Serial.println("s1 heating: emergency stop. status : " + String(status));
    }
    if (switchSystem.read() == LOW && switchStart.released()) {
        status = RESET; // go to reset if startswitch is off and system is on
        //Serial.println("s1 heating: reset. status : " + String(status));
    }
    if(TemperatureThreshold>-0.1) {
        status = REPORT;
        longheatingflag = 0;
        //Serial.println("s1 heating: report lh = 0. actual: status = " + String(status) + " lh = " + String(longheatingflag));
    }
    if(TemperatureThreshold<-4 && TemperatureThreshold>-8) {
        dutyCycleHeater = 100;
        PeriodHeater = 60000;
        longheatingflag =1;
        //Serial.println("s1 heating: duty = 100 period = 60000 lh = 1. actual : duty = " + String(dutyCycleHeater) + " period = " + String(PeriodHeater) + " lh = " + String(longheatingflag));
    }
    if(TemperatureThreshold<-8) {
        dutyCycleHeater = 100; PeriodHeater = 120000; longheatingflag = 1; // turn heater on for 2 mins
        //Serial.println("s1 heating: duty = 100 period = 120000 lh = 1. actual: duty = " + String(dutyCycleHeater) + " period = " + String(PeriodHeater) + " lh = " + String(longheatingflag));
    } 
    if(TemperatureThreshold>-4 && longheatingflag == 0) {
        dutyCycleHeater = 80; PeriodHeater = 25000; //on for 20 seconds and off for 5
        //Serial.println("s1 heating: duty = 80 period = 25000 lh = 0. actual: duty = " + String(dutyCycleHeater) + " period = " + String(PeriodHeater) + " lh = " + String(longheatingflag));
    }  
    if(TemperatureThreshold>-4 && longheatingflag == 1) {
        dutyCycleHeater = 0;  
        //Serial.println("s1 heating: thresh >-4 lh = 1. actual: thresh = " + String(TemperatureThreshold) + " lh = " + String(longheatingflag));
    }

    // s2
    //Serial.println("Entered s2 HEATING. actual status = " + String(status));
    PWMHeater(dutyCycleHeater, PeriodHeater);
    stateCooler = 0;    // TODO: Test
    stateHeater = 1;
    //Serial.println("s2 heating: stateHeater = 1 stateCooler = 0. actual: stateHeater = " + String(stateHeater) + " stateCooler = " + String(stateCooler));

}

void handleCoolingState() {
    //Serial.println("Entered s1 COOLING. actual status = " + String(status));
    heater.off();
    if (switchSystem.released()) {
        status = EMERGENCY_STOP;
        //Serial.println("s1 cooling: emergency stop. status : " + String(status));
    }
    if (switchSystem.read() == LOW && switchStart.released()) {
        status = RESET;
        //Serial.println("s1 cooling: reset. status : " + String(status));
    }
    if(TemperatureThreshold<0.4) {
        status = REPORT;
        //Serial.println("s1 cooling: thresh < 0.4. actual: thresh = " + String(TemperatureThreshold));
    }
    if(TemperatureThreshold > 1) {
        dutyCycleCooler = 100;
        PeriodCooler=2000;
        //Serial.println("s1 cooling: thresh > 1. actual: thresh = " + String(TemperatureThreshold));
    }
    if(TemperatureThreshold < 1 && TemperatureThreshold > 0.4) {
        dutyCycleCooler = 29;
        PeriodCooler=7000; // on for 2 seconds and off for 5
        //Serial.println("s1 cooling: 0.4 < thresh < 1. actual: thresh = " + String(TemperatureThreshold));
    } 
    longheatingflag = 0;

    // s2
    //Serial.println("Entered s2 COOLING. actual status = " + String(status));
    PWMCooler(dutyCycleCooler, PeriodCooler);
    stateHeater = 0;    // TODO: Test
    stateCooler = 1;
    //Serial.println("s2 COOLING: stateHeater = 0 stateCooler = 1. actual: stateHeater " + String(stateHeater) + " stateCooler = " + String(stateCooler));
}

void handleReportState() {
    //Serial.println("Entered s1 REPORT. actual status = " + String(status));
    if (switchSystem.released()) {
        status = EMERGENCY_STOP;
        //Serial.println("s1 report: emergency stop. actual = " + String(status));
    }
    if (switchSystem.read() == LOW && switchStart.released()) {
        status = RESET;
        //Serial.println("s1 reset: emergency stop. actual = " + String(status));
    }
    if (switchStart.read() == LOW)
    {
        if(TemperatureThreshold>0.4) {
            status = COOLING;
            //Serial.println("s1 reset: thresh > 0.4 status = COOLING. actual: thresh = " + String(TemperatureThreshold) + " status = " + String(status));
        }
        if(TemperatureThreshold<-0.1) {
            status = HEATING;
            //Serial.println("s1 reset: thresh < -0.1 status = HEATING. actual: thresh = " + String(TemperatureThreshold) + " status = " + String(status));
        }
    }
}

void handleEmergencyStopState() {
    //Serial.println("Entered s1 EMERGENCY_STOP. actual status = " + String(status));
    if (switchSystem.pressed() || switchSystem.held()) {
        status = RESET;
        //Serial.println("s1 emergency: reset. actual = " + String(status));
    }

    // s2
    //Serial.println("Entered s2 EMERGENCY_STOP. actual status = " + String(status));
    heater.off();
    cooler.off();
    stateHeater = 0;
    stateCooler = 0;
    displayLCDOff();
    longheatingflag =0;
    inputString ="";
    //Serial.println("s2 EMERGENCY: stateHeater = 0 stateCooler = 0 lh = 0. actual: stateHeater = " + String(stateHeater) + " stateCooler = " + String(stateCooler) + " lh = " + String(longheatingflag));
}

unsigned long lastUpdate = 0;
unsigned long updateInterval = 500;

void loop() {  

    unsigned long currentMillis = millis();
    if (currentMillis - lastUpdate >= updateInterval) {
        displayLCD(temperatureRoom, temperatureDesired);
        lastUpdate = currentMillis;
    }

    temperatureRoomOld = temperatureRoom;
    stateHeaterOld = stateHeater;
    stateCoolerOld = stateCooler;
    temperatureDesiredOld = temperatureDesired;

    // get latest room temp
    temperatureRoom = getTemperature();
    TemperatureThreshold = temperatureRoom - temperatureDesired;

    // run test sequence if active
    if (isTestRunning) {
        runCurrentSequence();
    }

    // Check if data is available on the serial port
    if (Serial.available() > 0) {
        // Read the incoming data in chunks instead of one character at a time
        int len = Serial.readBytesUntil('\n', incomingString, sizeof(incomingString) - 1);
        incomingString[len] = '\0'; // null-terminate the string

        Serial.print("Received string: ");
        Serial.println(incomingString);

        DeserializationError error = deserializeJson(jsonBuffer, incomingString);
        // Handle the input string (either a command or JSON)
        if (!error) {
            Serial.println("JSON detected, parsing...");
            parseTextFromJson(jsonBuffer);  // Parse the JSON
        } else {
            Serial.print("Deserialization failed: ");
            Serial.println(error.c_str());
            Serial.println("Command detected, parsing...");
            parseCommand(incomingString);  // Parse regular commands
        }
        //incomingString = "";  // Reset for the next command
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
