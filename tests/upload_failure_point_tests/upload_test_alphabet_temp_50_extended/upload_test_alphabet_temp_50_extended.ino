
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

