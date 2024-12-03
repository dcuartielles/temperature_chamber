void setup() {
    Serial.begin(9600);
}

void loop() {
    // Buffer for the full output
    String output = "";

    // Append the alphabet to the output
    for (char letter = 'A'; letter <= 'Z'; letter++) {
        output += letter;
    }

    // Compute the factorial of 5
    int number = 5;
    long result = factorial(number);

    // Append the factorial result to the output
    output += result;

    // Print the combined output in a single line
    Serial.println(output);

    // Delay before the next iteration
    delay(1500);
}

long factorial(int number) {
    if (number <= 1) return 1;
    else return number * factorial(number - 1);
}
