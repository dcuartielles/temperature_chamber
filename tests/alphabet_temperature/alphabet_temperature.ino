#include <Modulino.h>

ModulinoThermo thermo;

void setup() {
    Serial.begin(9600);

    Modulino.begin();
    thermo.begin();
}

void loop() {
    // Loop through the alphabet and lastly print the temperature measured by Modulino Thermo
    for (char letter = 'A'; letter <= 'Z'; letter++) {
        Serial.print(letter);
        delay(500);
    }
    float temperature = thermo.getTemperature();
    Serial.println(temperature);
    delay(1000);
}
