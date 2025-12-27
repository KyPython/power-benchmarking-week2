/*
 * Arduino Power Receiver for M2 Neural Engine Monitoring
 * 
 * Receives serial data in format: ANE_PWR:[value]\n
 * Displays on Serial Monitor and can be used with Serial Plotter
 * 
 * Hardware: Any Arduino-compatible board (Uno, Nano, etc.)
 * Baud Rate: 115200
 */

const unsigned long BAUD_RATE = 115200;
const unsigned long SERIAL_TIMEOUT = 1000; // 1 second timeout

String inputBuffer = "";
bool newDataAvailable = false;
float currentPower = 0.0;
unsigned long lastUpdateTime = 0;
unsigned long packetCount = 0;
unsigned long errorCount = 0;

void setup() {
  // Initialize serial communication
  Serial.begin(BAUD_RATE);
  
  // Wait for serial port to open (useful for native USB boards)
  while (!Serial) {
    delay(10);
  }
  
  // Clear any initial garbage
  Serial.flush();
  
  // Print startup message
  Serial.println();
  for (int i = 0; i < 50; i++) Serial.print("=");
  Serial.println();
  Serial.println("Arduino Power Receiver - Ready");
  Serial.println("Waiting for ANE_PWR data from Python...");
  Serial.println("Format: ANE_PWR:[value]\\n");
  for (int i = 0; i < 50; i++) Serial.print("=");
  Serial.println();
  Serial.println();
  
  // Optional: Blink LED to indicate ready (if board has built-in LED)
  pinMode(LED_BUILTIN, OUTPUT);
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
    delay(100);
  }
}

void loop() {
  // Read incoming serial data
  while (Serial.available() > 0) {
    char inChar = Serial.read();
    
    if (inChar == '\n') {
      // End of message - process the buffer
      processPowerData(inputBuffer);
      inputBuffer = "";
    } else if (inChar != '\r') {
      // Add character to buffer (ignore carriage return)
      inputBuffer += inChar;
      
      // Prevent buffer overflow
      if (inputBuffer.length() > 64) {
        Serial.print("ERROR: Buffer overflow, resetting...");
        inputBuffer = "";
        errorCount++;
      }
    }
  }
  
  // Check for timeout (no data received for a while)
  if (newDataAvailable) {
    unsigned long timeSinceUpdate = millis() - lastUpdateTime;
    if (timeSinceUpdate > SERIAL_TIMEOUT) {
      Serial.println("WARNING: No data received for 1+ seconds");
      newDataAvailable = false;
    }
  }
  
  // Optional: Blink LED to show activity (every 2 seconds if data is flowing)
  if (newDataAvailable && (millis() % 2000 < 50)) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(10);
    digitalWrite(LED_BUILTIN, LOW);
  }
  
  // Small delay to prevent busy-waiting
  delay(10);
}

void processPowerData(String data) {
  // Expected format: "ANE_PWR:123.45"
  data.trim(); // Remove any whitespace
  
  // Check if data starts with "ANE_PWR:"
  if (data.startsWith("ANE_PWR:")) {
    // Extract the power value
    String powerStr = data.substring(8); // Skip "ANE_PWR:"
    
    // Convert to float
    float powerValue = powerStr.toFloat();
    
    // Validate the value (ANE power should be reasonable: 0-5000 mW)
    if (powerValue >= 0 && powerValue <= 5000) {
      currentPower = powerValue;
      newDataAvailable = true;
      lastUpdateTime = millis();
      packetCount++;
      
      // Display on Serial Monitor
      Serial.print("ANE Power: ");
      Serial.print(powerValue, 2);
      Serial.print(" mW");
      Serial.print(" | Packets: ");
      Serial.print(packetCount);
      Serial.print(" | Errors: ");
      Serial.println(errorCount);
      
      // For Serial Plotter: Just send the number (one per line)
      // Uncomment the line below and comment out the Serial.print above
      // Serial.println(powerValue);
      
    } else {
      Serial.print("ERROR: Invalid power value: ");
      Serial.println(powerValue);
      errorCount++;
    }
  } else if (data.length() > 0) {
    // Received data but not in expected format
    Serial.print("ERROR: Unexpected format: ");
    Serial.println(data);
    errorCount++;
  }
}

