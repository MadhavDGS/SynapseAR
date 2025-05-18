#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "MAX30105.h"
#include "heartRate.h"
#include "spo2_algorithm.h"
#include <esp_now.h>
#include <WiFi.h>

// MAC Address of the receiver ESP32 (AR device)
uint8_t receiverMacAddress[] = {0xEC, 0x62, 0x60, 0x99, 0xC0, 0x40}; // AR device MAC address

// Data structure for sensor readings
typedef struct sensor_readings {
  float heartRate;
  int heartRateAvg;
  int spo2;
  int spo2Avg;
  float temperature;
  bool fallDetected;
  bool validReadings;
} sensor_readings;

// Create a sensor readings object
sensor_readings sensorData;

// ESP-NOW peer info
esp_now_peer_info_t peerInfo;

// Callback when data is sent
void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
  Serial.print("Last Packet Send Status: ");
  Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Delivery Success" : "Delivery Fail");
}

// I2C Pins for ESP32 - Using OLED pins for MAX30105 as well
#define OLED_SDA 21
#define OLED_SCL 22
#define MPU_SDA 18
#define MPU_SCL 19
// Using OLED pins for MAX30105
#define MAX_SDA OLED_SDA
#define MAX_SCL OLED_SCL

// Buzzer Pin
#define BUZZER_PIN 5

// MAX30105 Default I2C Address
#define MAX30105_ADDRESS 0x57

// Create separate I2C instances
TwoWire I2C_OLED_MAX = TwoWire(0); // Shared OLED and MAX30105 bus
TwoWire I2C_MPU = TwoWire(1);

// OLED Display Settings
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define SCREEN_ADDRESS 0x3C
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &I2C_OLED_MAX, OLED_RESET);

// MPU6050 Settings
const int MPU_ADDR = 0x68;
int16_t accelerometer_x, accelerometer_y, accelerometer_z;
int16_t gyro_x, gyro_y, gyro_z;
int16_t temperature;

// Fall detection parameters
#define FALL_THRESHOLD 0.46       // 30% less sensitive (0.35 * 1.3)
#define IMPACT_THRESHOLD 2.6     // 30% less sensitive (2.0 * 1.3)
#define MIN_FALL_DURATION 4      // Increased from 3 to 4 for more confirmation time
#define FALL_TIMEOUT 5000        // Time to keep fall alert active (5 seconds)
#define BUZZER_ALERT_TIME 10000  // 10 seconds buzzer duration
#define FALL_RECOVERY_CHECK 4    // Increased from 3 to 4 for more stable recovery check
bool fallDetected = false;
unsigned long fallDetectedTime = 0;
unsigned long fallStartTime = 0;
float accelerationMagnitude = 0;   // Total acceleration magnitude
float previousAccMagnitude = 0;    // For fall trend detection
float restingAccMagnitude = 0;     // Baseline at rest (should be ~1g)
float peakAcceleration = 0;        // Track peak during potential fall
bool potentialFall = false;        // Track fall state
#define FALL_SAMPLES 6             // Reduced samples for faster response
float accMagnitudeBuffer[FALL_SAMPLES] = {0}; // Buffer for smoothing
int accBufferIndex = 0;
#define REST_SAMPLES 20            // Fewer samples for faster startup
int restSampleCount = 0;

// Buzzer variables
bool buzzerActive = false;
unsigned long buzzerStartTime = 0;

// New fall detection variables from example code
float ax = 0, ay = 0, az = 0, gx = 0, gy = 0, gz = 0;
boolean fall = false; //stores if a fall has occurred
boolean trigger1 = false; //stores if first trigger (lower threshold) has occurred
boolean trigger2 = false; //stores if second trigger (upper threshold) has occurred
boolean trigger3 = false; //stores if third trigger (orientation change) has occurred
byte trigger1count = 0; //stores the counts past since trigger 1 was set true
byte trigger2count = 0; //stores the counts past since trigger 2 was set true
byte trigger3count = 0; //stores the counts past since trigger 3 was set true
int angleChange = 0;

// MAX30102 Settings
MAX30105 particleSensor;

// Heart Rate calculation variables
const byte RATE_SIZE = 4; // Increase this for more averaging. 4 is good.
byte rates[RATE_SIZE]; // Array of heart rates
byte rateSpot = 0;
long lastBeat = 0; // Time at which the last beat occurred
float beatsPerMinute;
int beatAvg;
byte pulseLED = 2; // Blink with heartbeat

// 15-second average variables
#define LONG_AVG_SIZE 15    // 15 entries for 15 seconds
int longRates[LONG_AVG_SIZE]; // Store 15 seconds of rates
int longRateIndex = 0;      // Current position in long-term array
int longRateAvg = 0;        // 15-second average
unsigned long lastLongRateUpdate = 0;  // Last time we updated long-term average
bool longRateReady = false; // Indicates if we have a full 15 seconds of data
int validLongRates = 0;     // Count of valid entries

// Enhanced Beat Detection Variables
long irValue = 0;
long lastIrValue = 0;
long delta = 0;
long valueSum = 0;
int valueCount = 0;
long threshold = 0;
bool isPeak = false;
bool wasPeak = false;
#define IR_THRESHOLD 500    // Reduced threshold for beat detection
#define BEAT_TIMEOUT 2500   // Maximum time between beats (in ms)
#define MIN_BRIGHTNESS 20   // Minimum LED brightness
#define MAX_BRIGHTNESS 240  // Maximum LED brightness
byte currentBrightness = 60; // Starting brightness
// Track IR values for slope detection
long irValues[4] = {0, 0, 0, 0};
bool slopeDown = false;
bool prevSlopeDown = false;
unsigned long lastSlope = 0;
// More robust beat detection
#define BEAT_WINDOW 8       // Window for beat detection analysis
long irWindow[BEAT_WINDOW]; // Store recent values
int windowIndex = 0;        // Current position in window

// For finger detection
bool fingerDetected = false;

// Page Navigation
#define NUM_PAGES 2  // Reduced to just SPO2 and heart rate pages
int currentPage = 0;

// Button Settings
const int BUTTON_PIN = 13;
bool buttonPressed = false;
bool lastButtonState = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50;

// SPO2 variables
uint32_t irBuffer[100]; //infrared LED sensor data
uint32_t redBuffer[100];  //red LED sensor data
int32_t bufferLength; //data length
int32_t spo2; //SPO2 value
int8_t validSPO2; //indicator to show if the SPO2 calculation is valid
int32_t spo2HeartRate; //heart rate value from SPO2 algorithm
int8_t validHeartRate; //indicator to show if the heart rate calculation is valid
unsigned long spo2StartTime = 0;
unsigned long heartRateStartTime = 0;
bool spo2Mode = false;
int spo2Readings[5] = {0, 0, 0, 0, 0}; // Store last 5 SPO2 readings
int spo2Index = 0;
int spo2Avg = 0;
bool spo2Ready = false;
bool announcedValidSPO2 = false; // Flag to track if we've announced valid SPO2

// Temperature variables
float currentTemperature = 0.0;
unsigned long lastTempCheck = 0;
#define TEMP_CHECK_INTERVAL 2000 // Check temperature every 2 seconds

// Function to scan for I2C devices
void scanI2CBus(TwoWire &wire, const char* busName) {
  byte error, address;
  int deviceCount = 0;
  
  Serial.print("Scanning I2C bus (");
  Serial.print(busName);
  Serial.println(")...");

  for(address = 1; address < 127; address++) {
    wire.beginTransmission(address);
    error = wire.endTransmission();
    
    if(error == 0) {
      Serial.print("Device found at address 0x");
      if(address < 16) Serial.print("0");
      Serial.print(address, HEX);
      
      // Known I2C addresses
      if(address == SCREEN_ADDRESS) Serial.print(" (OLED Display)");
      if(address == MPU_ADDR) Serial.print(" (MPU6050)");
      if(address == MAX30105_ADDRESS) Serial.print(" (MAX30105)");
      
      Serial.println();
      deviceCount++;
      delay(10);
    }
  }
  
  if(deviceCount == 0) {
    Serial.print("No I2C devices found on bus ");
    Serial.println(busName);
  }
}

void setup() {
  Serial.begin(115200);
  delay(500); // Longer delay for stable initialization
  Serial.println("Starting initialization...");
  
  // Set device as a Wi-Fi Station
  WiFi.mode(WIFI_STA);
  
  // Print MAC address once
  Serial.print("This device's MAC Address: ");
  Serial.println(WiFi.macAddress());
  
  // Initialize ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }
  
  // Register send callback
  esp_now_register_send_cb(OnDataSent);
  
  // Register peer
  memcpy(peerInfo.peer_addr, receiverMacAddress, 6);
  peerInfo.channel = 0;  
  peerInfo.encrypt = false;
  
  // Add peer        
  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("Failed to add peer");
    return;
  }
  
  // Initialize I2C buses
  I2C_OLED_MAX.begin(OLED_SDA, OLED_SCL);
  I2C_MPU.begin(MPU_SDA, MPU_SCL);
  
  // Set I2C clock speeds
  I2C_OLED_MAX.setClock(100000);
  I2C_MPU.setClock(100000);
  
  // Initialize buzzer pin
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW); // Ensure buzzer is off at startup
  
  // Scan I2C buses to debug
  scanI2CBus(I2C_OLED_MAX, "OLED/MAX");
  scanI2CBus(I2C_MPU, "MPU");
  
  // Initialize OLED
  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println(F("SSD1306 allocation failed"));
    for(;;);
  }

  // Clear the buffer
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0);
  display.println("Initializing...");
  display.display();
  delay(1000);

  // Initialize button pin
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  // Initialize MPU6050
  I2C_MPU.beginTransmission(MPU_ADDR);
  I2C_MPU.write(0x6B);
  I2C_MPU.write(0);
  I2C_MPU.endTransmission(true);
  
  // Initialize MAX30105 with simple heart rate monitoring setup
  pinMode(pulseLED, OUTPUT);

  display.clearDisplay();
  display.setCursor(0,0);
  display.println("Configuring MAX30105");
  display.println("Heart Rate Monitor");
  display.display();
  
  // Initialize MAX30105 on the OLED bus
  if (particleSensor.begin(I2C_OLED_MAX, I2C_SPEED_STANDARD)) {
    // Configure sensor with custom settings for both HR and SPO2
    byte ledBrightness = 60; // Options: 0=Off to 255=50mA
    byte sampleAverage = 4; // Options: 1, 2, 4, 8, 16, 32
    byte ledMode = 2; // Options: 1 = Red only, 2 = Red + IR, 3 = Red + IR + Green
    byte sampleRate = 100; // Options: 50, 100, 200, 400, 800, 1000, 1600, 3200
    int pulseWidth = 411; // Options: 69, 118, 215, 411
    int adcRange = 4096; // Options: 2048, 4096, 8192, 16384
    
    particleSensor.setup(ledBrightness, sampleAverage, ledMode, sampleRate, pulseWidth, adcRange);
    currentBrightness = ledBrightness;
    
    // Initialize temperature reading - MUST be after setup call
    particleSensor.enableDIETEMPRDY(); // Enable the temp ready interrupt (required)
    delay(100); // Short delay to let the sensor stabilize
    
    // Take initial temperature reading
    currentTemperature = readTemperature();
    lastTempCheck = millis();
    
    display.clearDisplay();
    display.setCursor(0,0);
    display.println("MAX30105 Ready!");
    display.println("Place finger on");
    display.println("sensor firmly");
    display.setCursor(0, 32);
    display.print("Temp: ");
    display.print(currentTemperature, 1);
    display.println(" C");
    display.display();

    Serial.println("MAX30105 configured for heart rate and SPO2 monitoring");
    Serial.println("Place your index finger on the sensor with steady pressure.");
    Serial.print("Initial sensor temperature: ");
    Serial.print(currentTemperature, 2);
    Serial.println(" °C");
  } else {
    display.clearDisplay();
    display.setCursor(0,0);
    display.println("MAX30105 not found!");
    display.println("Check connections");
    display.display();
    Serial.println("MAX30105 not found! Check connections.");
  }
  
  // Initialize heart rate array
  for (byte i = 0; i < RATE_SIZE; i++) {
    rates[i] = 0;
  }
  
  // Initialize 15-second avg array
  for (int i = 0; i < LONG_AVG_SIZE; i++) {
    longRates[i] = 0;
  }
  
  // Initialize fall detection buffer
  for (int i = 0; i < FALL_SAMPLES; i++) {
    accMagnitudeBuffer[i] = 0;
  }
  
  // Initialize SPO2 buffers
  bufferLength = 100;
  for (int i = 0; i < bufferLength; i++) {
    irBuffer[i] = 0;
    redBuffer[i] = 0;
  }
  
  // Start with SPO2 mode instead of heart rate
  spo2Mode = true;
  spo2StartTime = millis();
  
  // Test buzzer with short beep
  digitalWrite(BUZZER_PIN, HIGH);
  delay(300);
  digitalWrite(BUZZER_PIN, LOW);
  
  Serial.println("Fall detection enabled. Threshold: " + String(FALL_THRESHOLD) + ", Min duration: " + String(MIN_FALL_DURATION) + "ms");
  Serial.println("Buzzer alert will sound for " + String(BUZZER_ALERT_TIME/1000) + " seconds after fall detection");
  delay(2000);
}

void updateHeartRate() {
  // Store previous value
  lastIrValue = irValue;
  
  // Get the latest IR value
  irValue = particleSensor.getIR();
  
  // Check if a finger is on the sensor - higher threshold for ESP32 implementation
  fingerDetected = irValue > 50000;
  
  // If finger is detected
  if (fingerDetected) {
    // Auto-adjust brightness if needed
    if (irValue > 200000) {
      // Signal too strong, reduce brightness
      if (currentBrightness > MIN_BRIGHTNESS) {
        currentBrightness -= 5;
        particleSensor.setPulseAmplitudeRed(currentBrightness);
        particleSensor.setPulseAmplitudeIR(currentBrightness);
        Serial.print("Signal strong, reducing brightness: ");
        Serial.println(currentBrightness);
      }
    } else if (irValue < 30000) {
      // Signal too weak, increase brightness
      if (currentBrightness < MAX_BRIGHTNESS) {
        currentBrightness += 5;
        particleSensor.setPulseAmplitudeRed(currentBrightness);
        particleSensor.setPulseAmplitudeIR(currentBrightness);
        Serial.print("Signal weak, increasing brightness: ");
        Serial.println(currentBrightness);
      }
    }
    
    // Shift values in the window
    for (int i = 0; i < BEAT_WINDOW-1; i++) {
      irWindow[i] = irWindow[i+1];
    }
    irWindow[BEAT_WINDOW-1] = irValue;
    windowIndex++;
    
    // First collect enough data
    if (windowIndex > BEAT_WINDOW) {
      // Check for downward slopes (after rise) - indicating potential beats
      
      // Calculate average and max/min in window
      long sum = 0;
      long max = 0;
      long min = 1000000;
      
      for (int i = 0; i < BEAT_WINDOW; i++) {
        sum += irWindow[i];
        if (irWindow[i] > max) max = irWindow[i];
        if (irWindow[i] < min) min = irWindow[i];
      }
      
      long avg = sum / BEAT_WINDOW;
      
      // Adaptive threshold - base threshold is the average of the window
      // but we make it lower to detect smaller changes
      threshold = avg - (max - avg) / 4;
      
      // Check for a beat pattern:
      // 1. Signal goes up above threshold
      // 2. Then signal drops below threshold
      
      // Detect if we're in a downward slope after being in an upward slope
      bool currentDown = irWindow[BEAT_WINDOW-1] < irWindow[BEAT_WINDOW-2];
      bool prevUp = irWindow[BEAT_WINDOW-3] < irWindow[BEAT_WINDOW-2];
      
      // Store current pattern
      prevSlopeDown = slopeDown;
      slopeDown = currentDown;
      
      // Detect peak transition (up then down)
      if (prevUp && currentDown && !wasPeak && (millis() - lastSlope > 300)) {
        isPeak = true;
        wasPeak = true;
        lastSlope = millis();
        
        // Calculate BPM
        if (lastBeat != 0) {
          long delta = millis() - lastBeat;
          
          // Valid beat range
          if (delta > 300 && delta < BEAT_TIMEOUT) {
            beatsPerMinute = 60000.0 / delta;
            
            // Store if reasonable
            if (beatsPerMinute >= 40 && beatsPerMinute <= 180) {
              rates[rateSpot++] = (byte)beatsPerMinute;
              rateSpot %= RATE_SIZE;
              
              // Update 15-second average (once per second)
              unsigned long currentTime = millis();
              if (currentTime - lastLongRateUpdate >= 1000) {
                lastLongRateUpdate = currentTime;
                
                // Store current heart rate in long-term array
                longRates[longRateIndex] = (int)beatsPerMinute;
                longRateIndex = (longRateIndex + 1) % LONG_AVG_SIZE;
                
                // Count valid entries for full 15-second window
                if (!longRateReady) {
                  validLongRates++;
                  if (validLongRates >= LONG_AVG_SIZE) {
                    longRateReady = true;
                    
                    // Now calculate the first 15-second average
                    int sum = 0;
                    for (int i = 0; i < LONG_AVG_SIZE; i++) {
                      sum += longRates[i];
                    }
                    longRateAvg = sum / LONG_AVG_SIZE;
                    
                    // Print large formatted heart rate average
                    printLargeSerialValue("HEART RATE AVG", longRateAvg, true);
                  }
                } 
                else {
                  // We already have a full 15 seconds, calculate new average
                  int sum = 0;
                  for (int i = 0; i < LONG_AVG_SIZE; i++) {
                    sum += longRates[i];
                  }
                  longRateAvg = sum / LONG_AVG_SIZE;
                  
                  // Print large formatted heart rate average every 5 seconds
                  static unsigned long lastBigDisplay = 0;
                  if (currentTime - lastBigDisplay >= 5000) {
                    printLargeSerialValue("HEART RATE AVG", longRateAvg, true);
                    lastBigDisplay = currentTime;
                  }
                }
              }
              
              // Calculate short term average
              beatAvg = 0;
              for (byte x = 0; x < RATE_SIZE; x++) {
                beatAvg += rates[x];
              }
              beatAvg /= RATE_SIZE;
              
              // Visual feedback
              digitalWrite(pulseLED, !digitalRead(pulseLED));
              
              Serial.print("BEAT! Delta=");
              Serial.print(delta);
              Serial.print("ms, BPM=");
              Serial.println(beatsPerMinute);
            }
          }
          lastBeat = millis();
        } else {
          lastBeat = millis(); // First beat 
        }
      } else if (wasPeak && (millis() - lastSlope > 200)) {
        // Reset peak detection after some time
        wasPeak = false;
        isPeak = false;
      }
      
      // Timeout safety - if it's been too long, reset detection 
      if (lastBeat != 0 && millis() - lastBeat > BEAT_TIMEOUT) {
        wasPeak = false;
        isPeak = false;
      }
    }
    
  } else {
    // No finger detected
    digitalWrite(pulseLED, LOW);
    
    // Reset detection variables
    isPeak = false;
    wasPeak = false;
    windowIndex = 0;
    for (int i = 0; i < BEAT_WINDOW; i++) {
      irWindow[i] = 0;
    }
    
    // Reset BPM values after a while
    if (millis() - lastBeat > 5000) {
      lastBeat = 0;
      beatsPerMinute = 0;
      for (byte x = 0; x < RATE_SIZE; x++) {
        rates[x] = 0;
      }
      beatAvg = 0;
      
      // Also reset slope detection
      slopeDown = false;
      prevSlopeDown = false;
      
      // Reset 15-second average completely
      for (int i = 0; i < LONG_AVG_SIZE; i++) {
        longRates[i] = 0;
      }
      longRateAvg = 0;
      longRateReady = false;
      validLongRates = 0;
      longRateIndex = 0;
    }
  }
}

// Display heart rate page
void displayHeartRatePage() {
  // Title bar with centered text - smaller font
  display.setTextSize(1);
  display.setCursor(20, 0); // Centered for the small display
  display.println("Heart Rate Monitor");
  display.drawLine(0, 9, 128, 9, SSD1306_WHITE); // Separator line
  
  // Show fall alert if detected
  if (fallDetected && (millis() - fallDetectedTime < FALL_TIMEOUT)) {
    // Flash the warning with inverted colors
    if ((millis() / 500) % 2 == 0) {
      display.fillRect(0, 10, 128, 14, SSD1306_WHITE);
      display.setTextColor(SSD1306_BLACK);
      display.setCursor(10, 12);
      display.println("!!! FALL DETECTED !!!");
      display.setTextColor(SSD1306_WHITE);
    } else {
      display.setCursor(10, 12);
      display.println("!!! FALL DETECTED !!!");
    }
    return; // Skip the rest of the display if fall detected
  }
  
  if (fingerDetected) {
    // Heart rate data section - compact layout
    display.setTextSize(1);
    display.setCursor(10, 14);
    display.println("Heart Rate (BPM):");
    
    // Display BPM value - using size 2 instead of 3
    display.setTextSize(2);
    if (beatsPerMinute > 40 && beatsPerMinute < 180) {
      // Calculate position to center the text
      int textWidth;
      if (beatsPerMinute < 100) {
        textWidth = 2 * 12; // 2 digits * 12 pixels per digit (size 2)
      } else {
        textWidth = 3 * 12; // 3 digits * 12 pixels per digit (size 2)
      }
      
      display.setCursor((SCREEN_WIDTH - textWidth)/2, 25);
      display.println((int)beatsPerMinute);
    } else {
      // No valid reading
      display.setCursor(52, 25); // Center "--"
      display.println("--");
    }
    
    // Display heart icon that pulses with beat
    if (millis() - lastBeat < 500) {
      // Simple heart icon
      display.fillCircle(110, 18, 5, SSD1306_WHITE);
      display.fillCircle(100, 18, 5, SSD1306_WHITE);
      display.fillTriangle(95, 23, 115, 23, 105, 34, SSD1306_WHITE);
    }
    
    // Smaller 15-second average at the bottom
    display.setTextSize(1);
    display.setCursor(10, 42);
    display.print("15s Avg: ");
    if (longRateReady && longRateAvg > 0) {
      display.println(longRateAvg);
    } else {
      display.print("--");
      
      // Progress indicator for 15-second average
      if (!longRateReady) {
        display.setCursor(90, 42);
        int progress = (validLongRates * 100) / LONG_AVG_SIZE;
        display.print(progress);
        display.print("%");
      }
    }
  } else {
    // Prompt to place finger - centered
    display.setTextSize(1);
    display.setCursor(15, 20);
    display.println("Place finger on");
    display.setCursor(15, 30);
    display.println("sensor firmly");
    display.setCursor(15, 40);
    display.println("for heart reading");
  }
}

void displayMPU6050Page() {
  display.println("MPU6050 Data");
  display.println("------------");
  
  // Show fall alert if detected
  if (fallDetected && (millis() - fallDetectedTime < FALL_TIMEOUT)) {
    // Flash the warning with inverted colors
    if ((millis() / 500) % 2 == 0) {
      display.fillRect(0, 10, 128, 14, SSD1306_WHITE);
      display.setTextColor(SSD1306_BLACK);
      display.setCursor(10, 12);
      display.println("!!! FALL DETECTED !!!");
      display.setTextColor(SSD1306_WHITE);
    } else {
      display.setCursor(10, 12);
      display.println("!!! FALL DETECTED !!!");
    }
  }
  
  display.print("Acc X: "); display.println(accelerometer_x);
  display.print("Acc Y: "); display.println(accelerometer_y);
  display.print("Acc Z: "); display.println(accelerometer_z);
  
  // Raw amplitude from fall detection
  float Raw_Amp = sqrt(ax*ax + ay*ay + az*az);
  int Amp = Raw_Amp * 10;
  display.print("Amp: "); display.println(Amp);
  
  // Show triggers status
  display.print("T1:");
  display.print(trigger1 ? "ON" : "OFF");
  display.print(" T2:");
  display.print(trigger2 ? "ON" : "OFF");
  display.print(" T3:");
  display.println(trigger3 ? "ON" : "OFF");
  
  // Show angle change
  display.print("Angle Chg: ");
  display.println(angleChange);
  
  // Temperature in last line
  display.print("Temp: "); 
  display.println(temperature/340.00+36.53);
}

void displayMAXDebugPage() {
  display.println("MAX30105 Debug");
  display.println("-------------");
  
  // Show fall alert if detected
  if (fallDetected && (millis() - fallDetectedTime < FALL_TIMEOUT)) {
    // Flash the warning in the corner to not block debug info
    if ((millis() / 500) % 2 == 0) {
      display.fillRect(90, 0, 38, 9, SSD1306_WHITE);
      display.setTextColor(SSD1306_BLACK);
      display.setCursor(92, 1);
      display.println("FALL!");
  display.setTextColor(SSD1306_WHITE);
    } else {
      display.setCursor(92, 1);
      display.println("FALL!");
    }
  }
  
  display.print("IR: "); display.println(irValue);
  
  display.print("Finger: "); 
  display.println(fingerDetected ? "Detected" : "None");
  
  // Show current mode
  display.print("Mode: ");
  display.println(spo2Mode ? "SPO2" : "Heart Rate");
  
  if (spo2Mode) {
    // SPO2 debug info
    display.print("SPO2: "); 
    display.print(spo2);
    display.print(" (");
    display.print(validSPO2 ? "Valid" : "Invalid");
    display.println(")");
    
    // Show average in smaller font only on debug page
    display.print("Avg["); 
    display.print(spo2Index);
    display.print("/5]: ");
    display.println(spo2Avg);
    
    display.print("SPO2 HR: "); 
    display.print(spo2HeartRate);
    display.print(" (");
    display.print(validHeartRate ? "Valid" : "Invalid");
    display.println(")");
  } else {
    // Heart rate debug info
    display.print("BPM: "); display.println(beatsPerMinute);
    display.print("4-Avg: "); display.println(beatAvg);
    display.print("15s-Avg: "); display.println(longRateAvg);
    
    display.print("Last Beat: "); 
    display.print((millis() - lastBeat) / 1000.0, 1);
    display.println(" sec ago");
  }
  
  // Add peak detection details
  display.print("Thresh: "); 
  display.println(threshold);
  display.print("Peak: "); 
  display.println(isPeak ? "Yes" : "No");
  display.print("Slope: ");
  display.println(slopeDown ? "Down" : "Up");
  
  // Display time remaining in current mode
  unsigned long currentTime = millis();
  if (spo2Mode) {
    display.print("Next HR: ");
    display.print((20000 - (currentTime - spo2StartTime)) / 1000);
    display.println("s");
  } else {
    display.print("Next SPO2: ");
    display.print((30000 - (currentTime - heartRateStartTime)) / 1000);
    display.println("s");
  }
}

void updateMPU6050() {
  I2C_MPU.beginTransmission(MPU_ADDR);
  I2C_MPU.write(0x3B);
  I2C_MPU.endTransmission(false);
  I2C_MPU.requestFrom(MPU_ADDR, 7*2, true);
  
  accelerometer_x = I2C_MPU.read()<<8 | I2C_MPU.read();
  accelerometer_y = I2C_MPU.read()<<8 | I2C_MPU.read();
  accelerometer_z = I2C_MPU.read()<<8 | I2C_MPU.read();
  temperature = I2C_MPU.read()<<8 | I2C_MPU.read();
  gyro_x = I2C_MPU.read()<<8 | I2C_MPU.read();
  gyro_y = I2C_MPU.read()<<8 | I2C_MPU.read();
  gyro_z = I2C_MPU.read()<<8 | I2C_MPU.read();
  
  // Convert to g (±2g range) - using the reference code's calibration values
  ax = (accelerometer_x - 2050) / 16384.0;
  ay = (accelerometer_y - 77) / 16384.0;
  az = (accelerometer_z - 1947) / 16384.0;
  
  // Convert gyro values using reference code's calibration
  gx = (gyro_x + 270) / 131.07;
  gy = (gyro_y - 351) / 131.07;
  gz = (gyro_z + 136) / 131.07;
  
  // Calculate magnitude using reference code's method
  float Raw_Amp = sqrt(ax*ax + ay*ay + az*az);
  int Amp = Raw_Amp * 10;  // Multiplied by 10 because values are between 0 to 1
  
  // Debug output
  static unsigned long lastOutputTime = 0;
  if (millis() - lastOutputTime > 1000) {
    lastOutputTime = millis();
    Serial.print("Raw_Amp: ");
    Serial.print(Raw_Amp);
    Serial.print(" Amp: ");
    Serial.print(Amp);
    Serial.print(" ax: ");
    Serial.print(ax);
    Serial.print(" ay: ");
    Serial.print(ay);
    Serial.print(" az: ");
    Serial.println(az);
  }
  
  // Balanced fall detection with 30% less sensitivity
  if (Raw_Amp >= 1.95) {  // Increased from 1.5 to 1.95 (30% higher)
    // Direct fall detection for significant movements
    fall = true;
    fallDetected = true;
    fallDetectedTime = millis();
    
    // Activate buzzer alert
    buzzerActive = true;
    buzzerStartTime = millis();
    digitalWrite(BUZZER_PIN, HIGH);
    
    Serial.println("************************");
    Serial.println("**** FALL DETECTED! ****");
    Serial.println("Raw_Amp exceeded threshold!");
    Serial.print("Raw_Amp value: ");
    Serial.println(Raw_Amp);
    Serial.println("**** BUZZER ALERT ACTIVATED (10s) ****");
    Serial.println("************************");
    return;
  }
  
  // Multi-trigger fall detection for gentler movements
  // First trigger - 30% less sensitive
  if (Amp <= 4.55 && trigger2 == false) {  // Increased from 3.5 to 4.55
    trigger1 = true;
    Serial.println("TRIGGER 1 ACTIVATED");
  }
  
  // Count after trigger 1 activated
  if (trigger1 == true) {
    trigger1count++;
    
    // Second trigger - 30% less sensitive
    if (Amp >= 6.5) {  // Increased from 5.0 to 6.5
      trigger2 = true;
      Serial.println("TRIGGER 2 ACTIVATED");
      trigger1 = false;
      trigger1count = 0;
    }
  }
  
  // Count after trigger 2 activated
  if (trigger2 == true) {
    trigger2count++;
    
    // Calculate orientation change using gyroscope data
    angleChange = sqrt(gx*gx + gy*gy + gz*gz);
    
    // Third trigger - 30% less sensitive on minimum angle
    if (angleChange >= 19.5 && angleChange <= 400) {  // Increased from 15 to 19.5
      trigger3 = true;
      trigger2 = false;
      trigger2count = 0;
      Serial.print("Angle Change: ");
      Serial.println(angleChange);
      Serial.println("TRIGGER 3 ACTIVATED");
    }
  }
  
  // Process after trigger 3 activated
  if (trigger3 == true) {
    trigger3count++;
    
    // 30% less sensitive stable orientation check
    if (angleChange >= 0 && angleChange <= 7.15) {  // Increased from 5.5 to 7.15
      // Fall confirmed!
      fall = true;
      fallDetected = true;
      fallDetectedTime = millis();
      
      // Activate buzzer alert
      buzzerActive = true;
      buzzerStartTime = millis();
      digitalWrite(BUZZER_PIN, HIGH);
      
      trigger3 = false;
      trigger3count = 0;
      
      Serial.println("************************");
      Serial.println("**** FALL DETECTED! ****");
      Serial.println("Multi-trigger detection confirmed!");
      Serial.println("**** BUZZER ALERT ACTIVATED (10s) ****");
      Serial.println("************************");
    } else {
      // User regained normal orientation
      trigger3 = false;
      trigger3count = 0;
      Serial.println("TRIGGER 3 DEACTIVATED");
    }
  }
  
  // Very quick trigger reset to catch rapid changes
  if (trigger2count >= 3) {
    trigger2 = false;
    trigger2count = 0;
    Serial.println("TRIGGER 2 DEACTIVATED");
  }
  
  if (trigger1count >= 3) {
    trigger1 = false;
    trigger1count = 0;
    Serial.println("TRIGGER 1 DEACTIVATED");
  }
  
  // Reset fall detection after timeout
  if (fallDetected && (millis() - fallDetectedTime > FALL_TIMEOUT)) {
    fallDetected = false;
    Serial.println("Fall alert reset");
  }
}

void checkButton() {
  // Button functionality disabled as requested
  // This function is now a stub that does nothing
  return;
}

void displaySPO2Page() {
  // Title bar with centered text
  display.setTextSize(1);
  display.setCursor(30, 0); // Better centering for small display
  display.println("SPO2 Monitor");
  display.drawLine(0, 9, 128, 9, SSD1306_WHITE); // Separator line
  
  // Show fall alert if detected
  if (fallDetected && (millis() - fallDetectedTime < FALL_TIMEOUT)) {
    // Flash the warning with inverted colors
    if ((millis() / 500) % 2 == 0) {
      display.fillRect(0, 10, 128, 14, SSD1306_WHITE);
      display.setTextColor(SSD1306_BLACK);
      display.setCursor(10, 12);
      display.println("!!! FALL DETECTED !!!");
      display.setTextColor(SSD1306_WHITE);
    } else {
      display.setCursor(10, 12);
      display.println("!!! FALL DETECTED !!!");
    }
    return; // Skip the rest of the display if fall detected
  }
  
  if (fingerDetected) {
    // SPO2 data section - compact layout
    display.setTextSize(1);
    display.setCursor(15, 14);
    display.println("SPO2 Reading:");
    
    // Display SPO2 value - using size 2 instead of 3
    if (validSPO2) {
      if (spo2 < 80) {
        // For low SPO2, show warning
        display.setCursor(5, 24);
        display.println("LOW READING");
        display.setCursor(5, 34);
        display.println("ADJUST FINGER");
        display.setCursor(5, 44);
        display.println("POSITION");
      } else {
        // Display SPO2 value in medium font, centered
        display.setTextSize(2);
        
        // Calculate position to center the text
        int textWidth;
        if (spo2 < 100) {
          textWidth = 2 * 12; // 2 digits * 12 pixels per digit (size 2)
        } else {
          textWidth = 3 * 12; // 3 digits * 12 pixels per digit (size 2)
        }
        
        display.setCursor((SCREEN_WIDTH - textWidth)/2, 25);
        display.println(spo2);
        
        // Show % symbol
        display.setTextSize(1);
        display.setCursor(80, 30);
        display.println("%");
      }
    } else {
      // No valid reading
      display.setTextSize(2);
      display.setCursor(52, 25); // Center "--"
      display.println("--");
    }
    
    // Signal quality indicator at bottom
    display.setTextSize(1);
    display.setCursor(5, 42);
    display.print("Signal: ");
    display.print(irValue/1000);
    display.print("K");
    
    // Display simple pulse indicator
    if (isPeak) {
      display.fillCircle(110, 44, 4, SSD1306_WHITE);
    }
  } else {
    // Prompt to place finger - centered
    display.setTextSize(1);
    display.setCursor(15, 20);
    display.println("Place finger on");
    display.setCursor(15, 30);
    display.println("sensor firmly");
    display.setCursor(15, 40);
    display.println("for SPO2 reading");
  }
}

void updateSPO2() {
  // Store previous value
  lastIrValue = irValue;
  
  // Get the latest IR value
  irValue = particleSensor.getIR();
  
  // Check if a finger is on the sensor - higher threshold for ESP32 implementation
  fingerDetected = irValue > 50000;
  
  // If finger is detected
  if (fingerDetected) {
    // Auto-adjust brightness if needed
    if (irValue > 200000) {
      // Signal too strong, reduce brightness
      if (currentBrightness > MIN_BRIGHTNESS) {
        currentBrightness -= 5;
        particleSensor.setPulseAmplitudeRed(currentBrightness);
        particleSensor.setPulseAmplitudeIR(currentBrightness);
        Serial.print("Signal strong, reducing brightness: ");
        Serial.println(currentBrightness);
      }
    } else if (irValue < 30000) {
      // Signal too weak, increase brightness
      if (currentBrightness < MAX_BRIGHTNESS) {
        currentBrightness += 5;
        particleSensor.setPulseAmplitudeRed(currentBrightness);
        particleSensor.setPulseAmplitudeIR(currentBrightness);
        Serial.print("Signal weak, increasing brightness: ");
        Serial.println(currentBrightness);
      }
    }
    
    // Read sensor data
    if (particleSensor.available()) {
      // Read the IR and Red values
      redBuffer[bufferLength - 1] = particleSensor.getRed();
      irBuffer[bufferLength - 1] = particleSensor.getIR();
      particleSensor.nextSample();
      
      // Calculate heart rate and SPO2
      maxim_heart_rate_and_oxygen_saturation(irBuffer, bufferLength, redBuffer, &spo2, &validSPO2, &spo2HeartRate, &validHeartRate);
      
      // Only consider SPO2 valid if finger detected and algorithm says valid and value is reasonable
      validSPO2 = validSPO2 && fingerDetected && (spo2 > 0) && (spo2 <= 100);
      
      // If valid, announce it the first time
      if (validSPO2 && !announcedValidSPO2) {
        Serial.println("\n**** VALID SPO2 READING OBTAINED ****");
        Serial.print("SPO2 = ");
        Serial.println(spo2);
        announcedValidSPO2 = true;
      }
      
      // Check for low SPO2 values
      if (validSPO2 && spo2 < 80) {
        // Only print every 2 seconds to avoid spamming
        static unsigned long lastLowSpo2Warning = 0;
        if (millis() - lastLowSpo2Warning > 2000) {
          Serial.println("WARNING: LOW SPO2 DETECTED - ARM & FINGER POSITION NOT DETECTED PROPERLY");
          lastLowSpo2Warning = millis();
        }
      }
      
      // Shift buffer
      for (int i = 0; i < bufferLength - 1; i++) {
        redBuffer[i] = redBuffer[i + 1];
        irBuffer[i] = irBuffer[i + 1];
      }
      
      // If we have a valid SPO2 reading, store it
      if (validSPO2) {
        spo2Readings[spo2Index] = spo2;
        spo2Index = (spo2Index + 1) % 5;
        
        // Calculate average if we have enough readings
        if (spo2Index == 0) {
          int sum = 0;
          for (int i = 0; i < 5; i++) {
            sum += spo2Readings[i];
          }
          spo2Avg = sum / 5;
          spo2Ready = true;
          
          // Print large SPO2 value every 5 readings
          printLargeSerialValue("SPO2", spo2, validSPO2);
        }
      }
      
      // Visual feedback
      digitalWrite(pulseLED, !digitalRead(pulseLED));
    }
  } else {
    // No finger detected
    digitalWrite(pulseLED, LOW);
    
    // Reset SPO2 values
    spo2 = 0;
    validSPO2 = false;
    spo2HeartRate = 0;
    validHeartRate = 0;
    
    // Reset average calculation
    spo2Index = 0;
    spo2Ready = false;
    for (int i = 0; i < 5; i++) {
      spo2Readings[i] = 0;
    }
  }
}

// Function to print large formatted values to serial monitor
void printLargeSerialValue(const char* label, int value, bool valid) {
  Serial.println("\n=================================================");
  Serial.println("=================================================");
  Serial.print("==    ");
  Serial.print(label);
  Serial.print(": ");
  
  if (valid) {
    Serial.print(value);
  } else {
    Serial.print("--");
  }
  
  Serial.println("    ==");
  Serial.println("=================================================");
  Serial.println("=================================================\n");
}

// Function to read temperature from MAX30105
float readTemperature() {
  // Read temperature directly using the readTemperature function
  // This matches the example code from SparkFun
  float temperatureC = particleSensor.readTemperature();
  float temperatureF = particleSensor.readTemperatureF();
  
  // Debug output
  Serial.print("temperatureC=");
  Serial.print(temperatureC, 2);
  Serial.print(" temperatureF=");
  Serial.print(temperatureF, 2);
  Serial.println();
  
  return temperatureC;
}

// Function to handle buzzer alert for fall detection
void updateBuzzer() {
  unsigned long currentTime = millis();
  
  // Check if buzzer alert should be active
  if (buzzerActive) {
    // Check if it's time to turn off the buzzer
    if (currentTime - buzzerStartTime >= BUZZER_ALERT_TIME) {
      // Turn off buzzer after alert time
      digitalWrite(BUZZER_PIN, LOW);
      buzzerActive = false;
      Serial.println("Buzzer alert ended");
    } else {
      // Create alert pattern - alternating tone every 500ms
      if ((currentTime / 500) % 2 == 0) {
        digitalWrite(BUZZER_PIN, HIGH);
      } else {
        digitalWrite(BUZZER_PIN, LOW);
      }
    }
  }
}

void loop() {
  // Update sensors only, no button checks
  updateMPU6050();
  
  // Update buzzer state
  updateBuzzer();
  
  // Check temperature periodically
  unsigned long currentTime = millis();
  if (currentTime - lastTempCheck >= TEMP_CHECK_INTERVAL) {
    currentTemperature = readTemperature();
    lastTempCheck = currentTime;
  }
  
  // Update sensor data structure
  sensorData.heartRate = beatsPerMinute;
  sensorData.heartRateAvg = beatAvg;
  sensorData.spo2 = spo2;
  sensorData.spo2Avg = spo2Avg;
  sensorData.temperature = currentTemperature;
  sensorData.fallDetected = fallDetected;
  sensorData.validReadings = (validSPO2 || validHeartRate) && fingerDetected;
  
  // Send sensor data every 2 seconds
  static unsigned long lastDataSend = 0;
  if (currentTime - lastDataSend >= 2000) {
    esp_err_t result = esp_now_send(receiverMacAddress, (uint8_t *)&sensorData, sizeof(sensor_readings));
    if (result != ESP_OK) {
      Serial.println("Error sending the data");
    }
    lastDataSend = currentTime;
  }
  
  // Check if we need to switch between SPO2 and heart rate modes
  if (spo2Mode) {
    // In SPO2 mode
    // First, update SPO2 to get latest reading and finger status
    updateSPO2();
    
    // Only switch to heart rate mode if we've gotten a valid SPO2 reading above 80
    if (fingerDetected && validSPO2 && spo2 >= 80 && (currentTime - spo2StartTime >= 20000)) { 
      // 20 seconds in SPO2 mode AND valid reading AND finger detected AND SPO2 >= 80
      spo2Mode = false;
      heartRateStartTime = currentTime;
      
      // Display detailed information including temperature during mode switch
      Serial.println("\n===== SWITCHING FROM SPO2 TO HEART RATE MODE =====");
      Serial.print("Final SPO2: ");
      Serial.println(spo2);
      Serial.print("SPO2 Average: ");
      Serial.println(spo2Avg);
      Serial.print("temperatureC=");
      Serial.print(currentTemperature, 2);
      Serial.print(" temperatureF=");
      Serial.print(particleSensor.readTemperatureF(), 2);
      Serial.println("=================================================\n");
      
      // Force page change to heart rate when mode changes
      currentPage = 1;
      display.clearDisplay();
      display.setCursor(0, 0);
      display.println("Switching to");
      display.println("Heart Rate Mode");
      display.display();
      delay(1000);
    } else if (!fingerDetected) {
      // If no finger is detected, reset the SPO2 start time to effectively wait indefinitely
      spo2StartTime = currentTime;
      
      // Every 10 seconds, remind user to place finger
      static unsigned long lastReminderTime = 0;
      if (currentTime - lastReminderTime > 10000) {
        Serial.println("No finger detected - waiting for finger placement before continuing");
        Serial.print("temperatureC=");
        Serial.print(currentTemperature, 2);
        Serial.print(" temperatureF=");
        Serial.print(particleSensor.readTemperatureF(), 2);
        Serial.println();
        
        lastReminderTime = currentTime;
        
        // Visual reminder
        display.clearDisplay();
        display.setCursor(15, 20);
        display.setTextSize(1);
        display.println("PLEASE PLACE");
        display.setCursor(15, 30);
        display.println("YOUR FINGER ON");
        display.setCursor(15, 40);
        display.println("THE SENSOR");
        display.display();
        delay(1000);
      }
    } else if (validSPO2 && spo2 < 80) {
      // If SPO2 is below 80, prompt for better finger placement and don't switch
      spo2StartTime = currentTime; // Reset timer to stay in SPO2 mode
      
      // Every 5 seconds, remind user to adjust finger
      static unsigned long lastLowSpo2Reminder = 0;
      if (currentTime - lastLowSpo2Reminder > 5000) {
        Serial.println("SPO2 below 80 detected - requesting better finger/arm position");
        Serial.print("Current SPO2: ");
        Serial.println(spo2);
        Serial.print("temperatureC=");
        Serial.print(currentTemperature, 2);
        Serial.print(" temperatureF=");
        Serial.print(particleSensor.readTemperatureF(), 2);
        Serial.println();
        
        lastLowSpo2Reminder = currentTime;
        
        // Visual reminder
        display.clearDisplay();
        display.setCursor(5, 16);
        display.setTextSize(1);
        display.println("LOW SPO2 READING");
        display.setCursor(5, 28);
        display.println("PLEASE ADJUST");
        display.setCursor(5, 40);
        display.println("FINGER AND ARM");
        display.display();
        delay(1000);
      }
    } else if (!validSPO2 && (currentTime - spo2StartTime >= 60000) && fingerDetected) {
      // Even if finger is detected but no valid reading after 60 seconds,
      // don't switch but show a message and keep trying
      spo2StartTime = currentTime; // Reset timer to keep trying in SPO2 mode
      Serial.println("No valid SPO2 reading after 60 seconds, continuing to try");
      Serial.print("temperatureC=");
      Serial.print(currentTemperature, 2);
      Serial.print(" temperatureF=");
      Serial.print(particleSensor.readTemperatureF(), 2);
      Serial.println();
      
      // Visual message
      display.clearDisplay();
      display.setCursor(5, 16);
      display.setTextSize(1);
      display.println("NO VALID READING");
      display.setCursor(5, 28);
      display.println("ADJUST FINGER");
      display.setCursor(5, 40);
      display.println("POSITION");
      display.display();
      delay(1000);
    }
  } else {
    // In heart rate mode
    updateHeartRate();
    
    if (currentTime - heartRateStartTime >= 30000) { // 30 seconds in heart rate mode
      spo2Mode = true;
      spo2StartTime = currentTime;
      
      // Display detailed information including temperature during mode switch
      Serial.println("\n===== SWITCHING FROM HEART RATE TO SPO2 MODE =====");
      Serial.print("Final Heart Rate: ");
      Serial.println(beatsPerMinute);
      Serial.print("Heart Rate Average: ");
      Serial.println(beatAvg);
      Serial.print("Current Temperature: ");
      Serial.print(currentTemperature, 2);
      Serial.println(" °C");
      Serial.println("==================================================\n");
      
      // Reset SPO2 validity flag when starting a new SPO2 measurement cycle
      validSPO2 = false;
      
      // Reset the announcement flag for the next SPO2 cycle
      announcedValidSPO2 = false;
      
      // Force page change to SPO2 when mode changes
      currentPage = 0;
      display.clearDisplay();
      display.setCursor(0, 0);
      display.println("Switching to");
      display.println("SPO2 Mode");
      display.display();
      delay(1000);
    }
  }
  
  // Display current page
  display.clearDisplay();
  display.setCursor(0, 0);
  
  switch(currentPage) {
    case 0:  // SPO2 Page
      displaySPO2Page();
      break;
    case 1:  // Heart Rate Page
      displayHeartRatePage();
      break;
  }
  
  // Display compact status bar
  display.setTextSize(1);
  display.drawLine(0, 54, 128, 54, SSD1306_WHITE); // Bottom separator line
  
  // Left: Page indicator
  display.setCursor(2, 56);
  display.print(currentPage + 1);
  display.print("/");
  display.print(NUM_PAGES);
  
  // Center: Mode indicator with clear separation
  display.drawLine(32, 55, 32, 63, SSD1306_WHITE); // Left divider
  display.drawLine(96, 55, 96, 63, SSD1306_WHITE); // Right divider
  
  if (spo2Mode) {
    display.setCursor(48, 56);
    display.print("SPO2");
  } else {
    display.setCursor(54, 56);
    display.print("HR");
  }
  
  // Right: Time indicator or waiting status
  if (spo2Mode) {
    if (!fingerDetected) {
      display.setCursor(100, 56);
      display.print("WAIT");
    } else if (!validSPO2) {
      display.setCursor(100, 56);
      display.print("WAIT");
    } else if (spo2 < 80) {
      display.setCursor(100, 56);
      display.print("ADJ.");  // "Adjust" indicator for low SPO2
    } else {
      int timeLeft = 20 - ((millis() - spo2StartTime) / 1000);
      if (timeLeft < 0) timeLeft = 0;
      display.setCursor(104, 56);
      display.print(timeLeft);
      display.print("s");
    }
  } else {
    int timeLeft = 30 - ((millis() - heartRateStartTime) / 1000);
    if (timeLeft < 0) timeLeft = 0;
    display.setCursor(104, 56);
    display.print(timeLeft);
    display.print("s");
  }

  // Output to serial
  Serial.print("IR=");
  Serial.print(irValue);
  
  if (spo2Mode) {
    Serial.print(", SPO2=");
    Serial.print(spo2);
    Serial.print(", Valid=");
    Serial.print(validSPO2);
    Serial.print(", Finger=");
    Serial.print(fingerDetected ? "YES" : "NO");
    Serial.print(", AvgCalc[");
    Serial.print(spo2Index);
    Serial.print("]=");
    Serial.print(spo2Avg);
  } else {
    Serial.print(", BPM=");
    Serial.print(beatsPerMinute);
    Serial.print(", Avg=");
    Serial.print(beatAvg);
  }
  
  // Add fall detection data to serial output
  Serial.print(", Fall=");
  Serial.print(fallDetected ? "YES" : "no");
  Serial.print(", Amp=");
  Serial.print(sqrt(ax*ax + ay*ay + az*az) * 10);
  
  if (trigger1 || trigger2 || trigger3) {
    Serial.print(", Triggers=");
    if (trigger1) Serial.print("T1");
    if (trigger2) Serial.print("T2");
    if (trigger3) Serial.print("T3");
  }
  
  if (fingerDetected) {
    Serial.print(", Thresh=");
    Serial.print(threshold);
    Serial.print(", Slope=");
    Serial.print(slopeDown ? "Down" : "Up");
    Serial.print(isPeak ? " BEAT" : "");
  } else {
    Serial.print(" No finger?");
  }

  Serial.println();

  display.display();
  delay(50);  // Shorter delay for faster updates
}



