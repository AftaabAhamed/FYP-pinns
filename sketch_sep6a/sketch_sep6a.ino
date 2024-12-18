// Define the pins for the ultrasonic sensor
#define TRIG_PIN 3  // Trigger pin connected to D1
#define ECHO_PIN 2  // Echo pin connected to D2

// Define the pin for the flow rate sensor
#define FLOW_SENSOR_PIN 7  // Flow rate sensor signal pin connected to D7

// Variables for flow rate calculation
volatile int pulseCount = 0;     // Count the number of pulses from the flow sensor
float flowRate = 0.0;            // Flow rate in liters per minute (L/min)
unsigned long oldTime = 0;       // Time tracking for flow rate calculation
int pump_v = 0;
void IRAM_ATTR pulseCounter() {
  pulseCount++;  // Increment pulse count whenever an interrupt occurs
}

// Variable to store the duration and distance
long duration;
float distance;


// Define the pins for the motor control
#define ENA 4  // ENA pin connected to D3
#define IN1 5  // IN1 pin connected to D4
#define IN2 6  // IN2 pin connected to D5

void setup() {


// Set the flow sensor pin as input
  pinMode(FLOW_SENSOR_PIN, INPUT);
  
  // Attach an interrupt to the flow sensor pin on the rising edge
  attachInterrupt(digitalPinToInterrupt(FLOW_SENSOR_PIN), pulseCounter, RISING);
  
  // Initialize variables
  oldTime = millis();


   Serial.begin(9600);

  // Set the ultrasonic sensor pins as output and input
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  
  // Set the motor control pins as output
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  
  // Initialize motor to stop
  stopMotor();
}

void loop() {

 // Measure flow rate once every second
  if ((millis() - oldTime) > 1000) {
    // Detach the interrupt while processing the pulse count
    detachInterrupt(digitalPinToInterrupt(FLOW_SENSOR_PIN));

    // Calculate the flow rate in liters per minute (L/min)
    flowRate = ((1000.0 / (millis() - oldTime)) * pulseCount) / 7.5;  // 7.5 is the calibration factor for YF-S201 sensor

    // Print the flow rate to the serial monitor
    // Serial.print("Flow rate: ");
    // Serial.print(flowRate);
    // Serial.println(" L/min");

    // Reset the pulse count and time
    pulseCount = 0;
    oldTime = millis();
    
    // Re-attach the interrupt
    attachInterrupt(digitalPinToInterrupt(FLOW_SENSOR_PIN), pulseCounter, RISING);}

// Measure distance using ultrasonic sensor
  measureDistance();
  if (Serial.available()){
  pump_v = Serial.readString().toInt();
  }
  // Print the distance to the serial monitor
  // Serial.print("Distance: ");
  // Serial.print(distance);
  // Serial.println(" cm");
  String currentTime = String(millis());
  String output = currentTime + " " + String(flowRate) + " " + String(distance) ;
  Serial.println(output);
    
  // Delay before the next reading
   // Adjust delay as needed

  // Example: Run motor backward at 50% speed for 3 seconds
  runMotorBackward(pump_v); // PWM value for 50% speed
  
  delay(100);           // Run for 3 seconds
  // // Stop motor for 2 seconds
  // stopMotor();
  // delay(2000);
}

void measureDistance() {
  // Clear the trigger pin
  digitalWrite(TRIG_PIN, LOW); 
  delayMicroseconds(2);

  // Send a 10 microsecond pulse to trigger pin
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // Read the echo pin, return the sound wave travel time in microseconds
  duration = pulseIn(ECHO_PIN, HIGH);

  // Calculate the distance (speed of sound is 343 m/s or 0.034 cm/us)
  distance = (duration * 0.034) / 2;  // Divide by 2 for round-trip distance

}

// Function to run motor backward
void runMotorBackward(int speed) {
  analogWrite(ENA, speed);  // Set speed (0-255)
  digitalWrite(IN1, LOW);   // IN1 low
  digitalWrite(IN2, HIGH);  // IN2 high
}

// Function to stop the motor
void stopMotor() {
  analogWrite(ENA, 0);      // Disable speed
  digitalWrite(IN1, LOW);   // IN1 low
  digitalWrite(IN2, LOW);   // IN2 low
}

