#include "Wire.h" // This library allows you to communicate with I2C devices.

const int MPU_ADDR = 0x68; // I2C address of the MPU-6050. If AD0 pin is set to HIGH, the I2C address will be 0x69.

int16_t accelerometer_x, accelerometer_y, accelerometer_z; // variables for accelerometer raw data
int16_t gyro_x, gyro_y, gyro_z; // variables for gyro raw data
int16_t temperature; // variables for temperature data

char tmp_str[7]; // temporary variable used in convert function

// Output mode (set to true for Processing visualization)
bool processingMode = true;

char* convert_int16_to_str(int16_t i) { // converts int16 to string. Moreover, resulting strings will have the same length in the debug monitor.
  sprintf(tmp_str, "%6d", i);
  return tmp_str;
}

// Function to create a visual bar graph
String createBarGraph(int16_t value, int16_t maxValue) {
  // Normalize the value to a scale of 0-20 characters
  int barLength = map(abs(value), 0, maxValue, 0, 20);
  String bar = "";
  
  // Add direction indicator
  if (value < 0) {
    bar += "<";
  } else {
    bar += ">";
  }
  
  // Create the bar
  for (int i = 0; i < barLength; i++) {
    bar += "|";
  }
  
  return bar;
}

void setup() {
  Serial.begin(115200); // Higher baud rate for faster data transmission
  Wire.begin();
  Wire.beginTransmission(MPU_ADDR); // Begins a transmission to the I2C slave (GY-521 board)
  Wire.write(0x6B); // PWR_MGMT_1 register
  Wire.write(0); // set to zero (wakes up the MPU-6050)
  Wire.endTransmission(true);
}

void loop() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B); // starting with register 0x3B (ACCEL_XOUT_H) [MPU-6000 and MPU-6050 Register Map and Descriptions Revision 4.2, p.40]
  Wire.endTransmission(false); // the parameter indicates that the Arduino will send a restart. As a result, the connection is kept active.
  Wire.requestFrom(MPU_ADDR, 7*2, true); // request a total of 7*2=14 registers
  
  // "Wire.read()<<8 | Wire.read();" means two registers are read and stored in the same variable
  accelerometer_x = Wire.read()<<8 | Wire.read(); // reading registers: 0x3B (ACCEL_XOUT_H) and 0x3C (ACCEL_XOUT_L)
  accelerometer_y = Wire.read()<<8 | Wire.read(); // reading registers: 0x3D (ACCEL_YOUT_H) and 0x3E (ACCEL_YOUT_L)
  accelerometer_z = Wire.read()<<8 | Wire.read(); // reading registers: 0x3F (ACCEL_ZOUT_H) and 0x40 (ACCEL_ZOUT_L)
  temperature = Wire.read()<<8 | Wire.read(); // reading registers: 0x41 (TEMP_OUT_H) and 0x42 (TEMP_OUT_L)
  gyro_x = Wire.read()<<8 | Wire.read(); // reading registers: 0x43 (GYRO_XOUT_H) and 0x44 (GYRO_XOUT_L)
  gyro_y = Wire.read()<<8 | Wire.read(); // reading registers: 0x45 (GYRO_YOUT_H) and 0x46 (GYRO_YOUT_L)
  gyro_z = Wire.read()<<8 | Wire.read(); // reading registers: 0x47 (GYRO_ZOUT_H) and 0x48 (GYRO_ZOUT_L)
  
  // Calculate temperature in degrees Celsius
  float temp_celsius = temperature/340.00+36.53;
  
  if (processingMode) {
    // Send data in a format that Processing can easily parse
    // Format: "A:accelX,accelY,accelZ:G:gyroX,gyroY,gyroZ:T:temp"
    Serial.print("A:");
    Serial.print(accelerometer_x);
    Serial.print(",");
    Serial.print(accelerometer_y);
    Serial.print(",");
    Serial.print(accelerometer_z);
    Serial.print(":G:");
    Serial.print(gyro_x);
    Serial.print(",");
    Serial.print(gyro_y);
    Serial.print(",");
    Serial.print(gyro_z);
    Serial.print(":T:");
    Serial.println(temp_celsius);
  } else {
    // Original visual dashboard for Serial Monitor
    // Clear the serial monitor
    Serial.write(27);     // ESC command
    Serial.print("[2J");  // clear screen command
    Serial.write(27);
    Serial.print("[H");   // cursor to home command
  
    // Print a visual header
    Serial.println("=== MPU6050 VISUAL DASHBOARD ===");
    Serial.println();
    
    // Print accelerometer values with visual bar graphs
    Serial.print("ACCEL X: "); 
    Serial.print(convert_int16_to_str(accelerometer_x));
    Serial.print(" ");
    Serial.println(createBarGraph(accelerometer_x, 16000));
    
    Serial.print("ACCEL Y: "); 
    Serial.print(convert_int16_to_str(accelerometer_y));
    Serial.print(" ");
    Serial.println(createBarGraph(accelerometer_y, 16000));
    
    Serial.print("ACCEL Z: "); 
    Serial.print(convert_int16_to_str(accelerometer_z));
    Serial.print(" ");
    Serial.println(createBarGraph(accelerometer_z, 16000));
    
    Serial.println();
    
    // Print temperature with a simple indicator
    Serial.print("TEMP   : "); 
    Serial.print(temp_celsius);
    Serial.print(" °C  ");
    // Add a simple temperature indicator
    for (int i = 0; i < (int)(temp_celsius - 20); i++) {
      Serial.print("*");
    }
    Serial.println();
    
    Serial.println();
    
    // Print gyroscope values with visual bar graphs
    Serial.print("GYRO X : "); 
    Serial.print(convert_int16_to_str(gyro_x));
    Serial.print(" ");
    Serial.println(createBarGraph(gyro_x, 1000));
    
    Serial.print("GYRO Y : "); 
    Serial.print(convert_int16_to_str(gyro_y));
    Serial.print(" ");
    Serial.println(createBarGraph(gyro_y, 1000));
    
    Serial.print("GYRO Z : "); 
    Serial.print(convert_int16_to_str(gyro_z));
    Serial.print(" ");
    Serial.println(createBarGraph(gyro_z, 1000));
    
  Serial.println();
    Serial.println("=================================");
  }
  
  // delay
  delay(50); // Faster updates for Processing visualization
}
