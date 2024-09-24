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

// Defines
#define ONE_WIRE_BUS_1 A0  // temp sensor 1
#define ONE_WIRE_BUS_2 A1  // temp sensor 2
#define RELAY_COOLER 2
#define RELAY_HEATER 3
#define BUTTON_INCREMENT 5
#define BUTTON_DECREMENT 4
#define SWITCH_START 6
#define SWITCH_SYSTEM_STATE 7

// States for the state machine
#define RESET 0
#define HEATING 1
#define COOLING 2
#define REPORT 3
#define EMERGENCY_STOP 4

// Modes for the state machine
#define AUTOMATIC 0
#define MANUAL 1

// Define temperature limits
#define TEMPERATURE_MAX 100
#define TEMPERATURE_MIN 0


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

// Define Variables
double temperatureRoom;
double temperatureRoomOld;
double temperatureDesiredOld;
double temperatureDesired = 70;  // by default, we want to reach max temperature
float TemperatureThreshold = 0;
int longheatingflag = 0;
String inputString;




// Timing variables
unsigned long timerHeater = 0;
unsigned long timerCooler = 0;
unsigned long PeriodHeater = 0;
unsigned long PeriodCooler = 0;

// Heater and cooler states
int stateHeater = 0;
int stateCooler = 0;
int stateHeaterOld = 0;
int stateCoolerOld = 0;
int dutyCycleHeater = 0;
int dutyCycleCooler = 0;

// State machine variables
int status = EMERGENCY_STOP;
bool dataEvent = false;


void setup() {
    // Initialise Serial
    Serial.begin(9600);

    // Initialise thermocouples
    sensors1.begin();
    sensors2.begin();

    // Initialise LCD
    lcd.init();       // Initialize the LCD screen
                      //lcd.backlight();  // Turn on the backlight of lcd
    temperatureRoom = GetTemperature();
    showData();
}

void loop() {  
    temperatureRoomOld = temperatureRoom;
    stateHeaterOld = stateHeater;
    stateCoolerOld = stateCooler;
    temperatureDesiredOld = temperatureDesired;
    TemperatureThreshold= temperatureRoom-temperatureDesired;

    // Print status periodically
    //Serial.print("status: ");
    //Serial.println(status);

    // Read Serial input for commands and parse them
    if (Serial.available() > 0) {
        inputString = Serial.readStringUntil('\n'); // Read the input as a string until a newline character
        inputString.trim(); // Remove any leading/trailing whitespace

        Serial.println("Input available, parsing command...");
        parseCommand(inputString); // Process the command
    }  

    switch (status) {
        case RESET:
            if (switchSystem.released() || switchSystem.read() == HIGH) status = EMERGENCY_STOP; // shut everything down
            if (switchStart.pressed() || switchStart.held()) status = REPORT; // check tempertaure  and report result
            changeTemperature();
            break;
        case HEATING:
            if (switchSystem.released()) status = EMERGENCY_STOP;
            if (switchSystem.read() == LOW && switchStart.released()) status = RESET; // go to reset if startswitch is off and system is on
            if(TemperatureThreshold>-0.1) {status = REPORT;longheatingflag =0;}

            if(TemperatureThreshold<-4 && TemperatureThreshold>-8) {dutyCycleHeater = 100; PeriodHeater = 60000; longheatingflag =1;}
            if(TemperatureThreshold<-8) {dutyCycleHeater = 100; PeriodHeater = 120000; longheatingflag =1;} // turn heater on for 2 mins
            if(TemperatureThreshold>-4 && longheatingflag == 0) {dutyCycleHeater = 80; PeriodHeater = 25000;}  //on for 20 seconds and off for 5
            if(TemperatureThreshold>-4 && longheatingflag == 1) dutyCycleHeater = 0;  
            break;
        case COOLING:
            if (switchSystem.released()) status = EMERGENCY_STOP;
            if (switchSystem.read() == LOW && switchStart.released()) status = RESET;
            if(TemperatureThreshold<0.4) status = REPORT;

            if(TemperatureThreshold>1) {dutyCycleCooler = 100;PeriodCooler=2000;}
            if(TemperatureThreshold<1 && TemperatureThreshold>0.4) {dutyCycleCooler = 29; PeriodCooler=7000;} // on for 2 seconds and off for 5
            longheatingflag =0;
            break;
        case REPORT:
            if (switchSystem.released()) status = EMERGENCY_STOP;
            if (switchSystem.read() == LOW && switchStart.released()) status = RESET;
            if (switchStart.read() == LOW)
            {
                if(TemperatureThreshold>0.4) status = COOLING;
                if(TemperatureThreshold<-0.1) status = HEATING;
            }
            break;
        case EMERGENCY_STOP:
            if (switchSystem.pressed() || switchSystem.held()) status = RESET;
            break;
    }

    // render outputs based in overall status and such
    switch (status) {
        case RESET:
            heater.off();
            cooler.off();
            stateHeater = 0;
            stateCooler = 0;
            longheatingflag =0;
            showData();
            break;
        case HEATING:
            PWMHeater(dutyCycleHeater, PeriodHeater);
            stateHeater = 1;
            showData();

            //Read the serial input so that in case we input a value when not in reset case, we dont take it consideration for the desired temperature change
            //if (Serial.available() > 0) Serial.read(); // Flush serial buffer by reading and discarding any incoming data
            break;
        case COOLING:
            PWMCooler(dutyCycleCooler, PeriodCooler);
            stateCooler = 1;
            showData();

            //Read the serial input so that in case we input a value when not in reset case, we dont take it consideration for the desired temperature change
            //if (Serial.available() > 0) Serial.read(); // Flush serial buffer by reading and discarding any incoming data
            break;
        case REPORT:
            showData();

            //Read the serial input so that in case we input a value when not in reset case, we dont take it consideration for the desired temperature change
            //if (Serial.available() > 0) Serial.read(); // Flush serial buffer by reading and discarding any incoming data
            break;
        case EMERGENCY_STOP:
            heater.off();
            cooler.off();
            stateHeater = 0;
            stateCooler = 0;
            displayLCDOff();
            longheatingflag =0;
            inputString ="";

            //Read the serial input so that in case we input a value when not in reset case, we dont take it consideration for the desired temperature change
            //if (Serial.available() > 0) Serial.read(); // Flush serial buffer by reading and discarding any incoming data
            break;
    }
}

void showData() {
    temperatureRoom = GetTemperature();
    displayLCD(temperatureRoom,temperatureDesired);
    // decide whether there is a dataEvent
    if(abs(temperatureRoomOld - temperatureRoom) > 0.1 || (temperatureDesiredOld - temperatureDesired)!=0 || stateHeaterOld != stateHeater || stateCoolerOld != stateCooler) dataEvent =1; // if the temp gradient is more than 0.1 deg
    else dataEvent = 0;
    if (dataEvent) {
        displaySerial();
    }
}

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

float GetTemperature() {
    float roomTemperature = 0;

    // Request temperatures from both sensors

    sensors1.setWaitForConversion(false);
    sensors2.setWaitForConversion(false);
    sensors1.requestTemperatures();
    sensors2.requestTemperatures();

    // get average room_temperature
    roomTemperature = (sensors1.getTempCByIndex(0) + sensors2.getTempCByIndex(0)) / 2;
    return roomTemperature;
}

bool isTemperatureReached(float targetTemp, float currentTemp) {
    return abs(targetTemp - currentTemp) <= 0.1;
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

void displayLCDOff() {
    lcd.noBacklight();  // turn off backlight
    lcd.noDisplay();
}

// dutyCycle has to be 0..100
void PWMHeater(int dutyCycle, unsigned long PeriodHeater) {
    if (millis() - timerHeater > dutyCycle * PeriodHeater / 100) heater.off();
    else heater.on();
    if (millis() - timerHeater > PeriodHeater) timerHeater = millis();
}

// dutyCycle has to be 0..100

void PWMCooler(int dutyCycle, unsigned long PeriodCooler) {
    if (millis() - timerCooler > dutyCycle * PeriodCooler / 100) cooler.off();
    else cooler.on();
    if (millis() - timerCooler > PeriodCooler) timerCooler = millis();
}

void displayStatus() {
    Serial.print("status: ");
    Serial.println(status);
}

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
    else if (command == "GET TEMP") {
        Serial.println("Room Temperature: " + String(temperatureRoom));
    }
    else if (command == "IS TEMP REACHED") {
        //Serial.println(isTemperatureReached(float targetTemp, float currentTemp))
    }
    else if (command == "SHOW DATA") {
        showData();
    }
    //displayStatus();
}

