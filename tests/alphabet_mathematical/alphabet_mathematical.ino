
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

    // Perform a computation (factorial of 5 == 120)
    int number = 5;
    long result = factorial(number);
    Serial.println(result);
    delay(1000);
}

long factorial(int number) {
    if (number <= 1) return 1;
    else return number * factorial(number - 1);
}
