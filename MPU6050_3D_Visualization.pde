import processing.serial.*;

Serial myPort;  // Create object from Serial class
String val;     // Data received from the serial port
float[] accel = new float[3];  // Accelerometer data [x, y, z]
float[] gyro = new float[3];   // Gyroscope data [x, y, z]
float temp;                   // Temperature data

// Cube properties
float cubeSize = 100;
float rotX = 0;
float rotY = 0;
float rotZ = 0;

// Constants for complementary filter
float alpha = 0.98;
float dt = 0.05; // 50ms update rate

// Overall rotation values
float pitch = 0;
float roll = 0;
float yaw = 0;

void setup() {
  size(800, 600, P3D);
  
  // List all available serial ports
  printArray(Serial.list());
  
  // Select the correct port:
  // Replace "0" with the index of your Arduino's port in the list printed above
  String portName = Serial.list()[0];
  myPort = new Serial(this, portName, 115200);
  myPort.bufferUntil('\n');  // Read data until a newline character
  
  textSize(16);
  fill(255);
}

void draw() {
  background(0);
  
  // Set up lights
  lights();
  ambientLight(50, 50, 50);
  directionalLight(255, 255, 255, 0, -1, -1);
  
  // Display data as text
  textAlign(LEFT);
  text("Accelerometer: X=" + nf(accel[0], 0, 2) + " Y=" + nf(accel[1], 0, 2) + " Z=" + nf(accel[2], 0, 2), 20, 30);
  text("Gyroscope: X=" + nf(gyro[0], 0, 2) + " Y=" + nf(gyro[1], 0, 2) + " Z=" + nf(gyro[2], 0, 2), 20, 60);
  text("Temperature: " + nf(temp, 0, 2) + "°C", 20, 90);
  text("Orientation: Pitch=" + nf(degrees(pitch), 0, 2) + "° Roll=" + nf(degrees(roll), 0, 2) + "° Yaw=" + nf(degrees(yaw), 0, 2) + "°", 20, 120);
  
  // Center the coordinate system
  translate(width/2, height/2, 0);
  
  // Apply rotations based on calculated orientation
  rotateX(pitch);
  rotateZ(roll);
  rotateY(yaw);
  
  // Draw coordinate system
  stroke(255, 0, 0);
  line(0, 0, 0, 200, 0, 0); // X-axis (red)
  stroke(0, 255, 0);
  line(0, 0, 0, 0, 200, 0); // Y-axis (green)
  stroke(0, 0, 255);
  line(0, 0, 0, 0, 0, 200); // Z-axis (blue)
  
  // Draw the 3D cube representing the sensor
  noStroke();
  
  // Top face (yellow)
  fill(255, 255, 0);
  beginShape();
  vertex(-cubeSize/2, -cubeSize/2, -cubeSize/2);
  vertex(cubeSize/2, -cubeSize/2, -cubeSize/2);
  vertex(cubeSize/2, -cubeSize/2, cubeSize/2);
  vertex(-cubeSize/2, -cubeSize/2, cubeSize/2);
  endShape(CLOSE);
  
  // Bottom face (cyan)
  fill(0, 255, 255);
  beginShape();
  vertex(-cubeSize/2, cubeSize/2, -cubeSize/2);
  vertex(cubeSize/2, cubeSize/2, -cubeSize/2);
  vertex(cubeSize/2, cubeSize/2, cubeSize/2);
  vertex(-cubeSize/2, cubeSize/2, cubeSize/2);
  endShape(CLOSE);
  
  // Front face (magenta)
  fill(255, 0, 255);
  beginShape();
  vertex(-cubeSize/2, -cubeSize/2, cubeSize/2);
  vertex(cubeSize/2, -cubeSize/2, cubeSize/2);
  vertex(cubeSize/2, cubeSize/2, cubeSize/2);
  vertex(-cubeSize/2, cubeSize/2, cubeSize/2);
  endShape(CLOSE);
  
  // Back face (blue)
  fill(0, 0, 255);
  beginShape();
  vertex(-cubeSize/2, -cubeSize/2, -cubeSize/2);
  vertex(cubeSize/2, -cubeSize/2, -cubeSize/2);
  vertex(cubeSize/2, cubeSize/2, -cubeSize/2);
  vertex(-cubeSize/2, cubeSize/2, -cubeSize/2);
  endShape(CLOSE);
  
  // Left face (green)
  fill(0, 255, 0);
  beginShape();
  vertex(-cubeSize/2, -cubeSize/2, -cubeSize/2);
  vertex(-cubeSize/2, -cubeSize/2, cubeSize/2);
  vertex(-cubeSize/2, cubeSize/2, cubeSize/2);
  vertex(-cubeSize/2, cubeSize/2, -cubeSize/2);
  endShape(CLOSE);
  
  // Right face (red)
  fill(255, 0, 0);
  beginShape();
  vertex(cubeSize/2, -cubeSize/2, -cubeSize/2);
  vertex(cubeSize/2, -cubeSize/2, cubeSize/2);
  vertex(cubeSize/2, cubeSize/2, cubeSize/2);
  vertex(cubeSize/2, cubeSize/2, -cubeSize/2);
  endShape(CLOSE);
}

void serialEvent(Serial myPort) {
  try {
    // Read the incoming data
    String inString = myPort.readStringUntil('\n');
    
    if (inString != null) {
      // Remove any whitespace
      inString = trim(inString);
      
      // Parse the incoming data format "A:accelX,accelY,accelZ:G:gyroX,gyroY,gyroZ:T:temp"
      if (inString.startsWith("A:")) {
        // Split by sections
        String[] sections = split(inString, ':');
        
        if (sections.length >= 6) {
          // Parse accelerometer data
          String[] accelData = split(sections[1], ',');
          if (accelData.length >= 3) {
            accel[0] = float(accelData[0]);
            accel[1] = float(accelData[1]);
            accel[2] = float(accelData[2]);
          }
          
          // Parse gyroscope data
          String[] gyroData = split(sections[3], ',');
          if (gyroData.length >= 3) {
            gyro[0] = float(gyroData[0]);
            gyro[1] = float(gyroData[1]);
            gyro[2] = float(gyroData[2]);
          }
          
          // Parse temperature
          temp = float(sections[5]);
          
          // Calculate orientation using complementary filter
          // Scale values to appropriate units
          // Accelerometer scaling - assume ±2g range for 16-bit values
          float accelScaleFactor = 1.0 / 16384.0; // 2g / 32768
          float ax = accel[0] * accelScaleFactor;
          float ay = accel[1] * accelScaleFactor;
          float az = accel[2] * accelScaleFactor;
          
          // Gyroscope scaling - assume ±250°/s range for 16-bit values
          float gyroScaleFactor = 1.0 / 131.0; // 250°/s / 32768
          float gx = radians(gyro[0] * gyroScaleFactor);
          float gy = radians(gyro[1] * gyroScaleFactor);
          float gz = radians(gyro[2] * gyroScaleFactor);
          
          // Calculate pitch and roll from accelerometer (rotation around X and Z axis)
          float accelPitch = atan2(ay, sqrt(ax*ax + az*az));
          float accelRoll = atan2(-ax, sqrt(ay*ay + az*az));
          
          // Integrate gyroscope data to get rotation
          pitch = alpha * (pitch + gx * dt) + (1.0 - alpha) * accelPitch;
          roll = alpha * (roll + gy * dt) + (1.0 - alpha) * accelRoll;
          yaw += gz * dt; // Gyro only for yaw as accelerometer can't detect rotation around Y axis
        }
      }
    }
  } catch (Exception e) {
    println("Error parsing serial data: " + e.toString());
  }
} 