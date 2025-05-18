# Synapse AR - Augmented Reality Healthcare Assistant

## Problem Statement: The Growing Need for Elderly-Centric Assistive Technology

### The Challenge
- Over 55 million people worldwide are living with dementia, expected to rise to 139 million by 2050
- India alone has more than 5.3 million dementia patients
- Elderly individuals face critical issues like:
  - Memory loss, confusion, and disorientation
  - Missed medications and disrupted daily routines
  - High risk of undetected falls and health deterioration
- Families and caregivers struggle with continuous monitoring and timely intervention

### The Necessity
There is a pressing need for an intelligent, wearable system that can:
- Continuously monitor health
- Detect emergencies in real time
- Provide caregivers with remote access and control
- Predict and prevent potential health crises using AI

### Our Innovation
As vision is one of the first senses to decline with age, most elderly individuals already rely on glasses. Leveraging this behavior, we have developed an innovative smart glasses-based solution that integrates:
- SpO2, heart rate, and body temperature sensors to track health and trigger alerts or predictive warnings
- An accelerometer for accurate fall detection
- AR (Augmented Reality) technology embedded in standard eyewear, with hands-free control combining comfort with cutting-edge functionality

This fusion of familiar eyewear with smart assistive technology creates a non-intrusive, always-on support system for elderly individuals. It not only enhances safety and independence but also provides peace of mind for families and caregivers through real-time monitoring and intelligent alerts.

## Proposed Solution - Synapse AR

We have designed Synapse AR as an integrated AI-driven AR wearable device to support elderly individuals and assist caregivers through real-time monitoring, alerting, and health prediction. With software and hardware integration with AI, Synapse AR is:

### Capable Of
- Continuous heart rate, SpO2, and body temperature tracking to detect signs of abnormalities and act accordingly
- Fall detection using accelerometer and motion
- AI-based health prediction models to assess potential risk of heart disease and diabetes
- Real-time alerts for critical conditions (e.g., low heart rate, fall detected)
- A web-based platform for guardians to:
  - Monitor health remotely
  - Receive emergency alerts
  - Update daily reminders, medications, or schedules

This solution provides independence to elderly people while giving caregivers full knowledge and data with peace of mind.

### Why Now?
- Increasing global elderly population requires scalable assistive tech solutions
- AI integration into healthcare is gaining regulatory support and adoption
- Rising demand for smart, connected health devices in both urban and rural contexts
- Lack of affordable, wearable AR-based health monitoring systems tailored for eldercare

### Target Users

**Primary Users:**
- Elderly individuals living independently or with mild cognitive impairment
- Patients managing chronic health conditions such as cardiovascular disease

**Secondary Users:**
- Guardians and caregivers needing real-time visibility into the health of loved ones
- Healthcare providers offering remote care or follow-up services

**Tertiary Market:**
- Elder care homes, assisted living facilities, clinics, and telehealth services

## Project Overview
Synapse AR is an augmented reality healthcare assistant designed to enhance patient care through wearable technology. The system combines specialized hardware running on ESP32 with computer vision capabilities and integrates with a web interface for monitoring health metrics. It focuses on medication management, health monitoring, and obstacle detection to improve quality of life for users.

## Key Components

### Hardware
- **ESP32 Microcontroller**: Controls the main wearable device functions
- **OLED Display**: SSD1306 display for user interface
- **GPS Module**: NEO-6M for location tracking
- **Ultrasonic Sensor**: Obstacle detection for navigation assistance
- **LDR Sensor**: Wear detection and auto-brightness control
- **Buzzer**: Audio alerts for obstacle detection
- **Heart Rate & SpO2 Sensor**: Health metric monitoring
- **Body Temperature Sensor**: Continuous temperature monitoring
- **Camera**: Medicine recognition and gesture detection

### Software
1. **AR Firmware (ar.ino)**:
   - ESP32 Arduino firmware for the wearable device
   - Multi-page UI system showing medicines, schedule, contact info, heart rate, time, calendar
   - Gesture-based page switching
   - Built-in obstacle detection with wear-aware alert system
   - GPS location tracking
   - Serial command interface

2. **Integrated AR Vision System (integrated_ar.py)**:
   - Computer vision with OpenCV
   - Google Gemini AI for medicine recognition
   - Gesture detection for hands-free control
   - Medicine schedule management
   - Interfaces with the AR hardware via serial connection

3. **Web Interface (synapse_web.py)**:
   - Flask-based web dashboard
   - Live health metrics visualization
   - Medication and schedule management
   - GPS location tracking
   - Health prediction models

4. **Telegram Alerts System (telegram_alerts.py)**:
   - Remote health monitoring
   - Real-time alerts for critical health events:
     - High temperature (>38°C)
     - Abnormal heart rate (<50 or >120 BPM)
     - Low blood oxygen (<95%)
     - Fall detection
   - Command interface for managing alerts

## Features

### Health Monitoring
- **Vital Signs Tracking**: Heart rate, SpO2, temperature
- **Body Temperature Monitoring**: Continuous tracking with alerts for fever
- **Fall Detection**: Immediate alerts when falls are detected
- **Emergency Contacts**: Quick access to emergency information

### Medication Management
- **Medicine Schedule**: Visual reminders for medication timing
- **Medicine Recognition**: AI-powered identification of medications
- **Medication Tracking**: Records when medications have been taken

### Navigation Assistance
- **Obstacle Detection**: Distance-based warning system with audio feedback
- **Wear-Sensitive Alerts**: Different audio alert patterns when worn vs. not worn
- **GPS Tracking**: Location monitoring for caregivers

### User Interface
- **Multi-Page Display**: Easy navigation between different information screens
- **Auto-Brightness**: Ambient light adaptation for optimal viewing
- **Gesture Control**: Hands-free page switching with simple gestures
- **Time & Calendar**: Built-in timekeeper with date information

### Remote Monitoring
- **Web Dashboard**: Browser-based monitoring interface
- **Telegram Alerts**: Instant messaging for critical health events
- **Data Visualization**: Clear presentation of health trends

## Setup Instructions

### Hardware Setup
1. **Components Assembly**:
   - Connect the OLED display (SPI: CS=5, DC=4, RST=16)
   - Connect LDR sensor to GPIO32
   - Connect ultrasonic sensor (TRIG=26, ECHO=27)
   - Connect buzzer to GPIO25
   - Connect GPS module (RX=12, TX=13)
   - Connect physical button to GPIO17

2. **ESP32 Firmware Installation**:
   - Install Arduino IDE with ESP32 board support
   - Install required libraries:
     - Adafruit_GFX
     - Adafruit_SSD1306
     - SPI
     - EEPROM
     - TinyGPS++
     - ESP-NOW
     - WiFi
   - Upload ar.ino to the ESP32

### Software Setup

1. **Python Environment**:
   ```bash
   # Create virtual environment
   python -m venv .venv1
   source .venv1/bin/activate  # On Windows: .venv1\Scripts\activate

   # Install required packages
   pip install pyTelegramBotAPI requests flask opencv-python numpy mediapipe google-generativeai pillow serial
   ```

2. **Telegram Bot Setup**:
   - Create a Telegram bot using BotFather
   - Get the API token
   - Create a group and add the bot
   - Get the group chat ID
   - Update the token and chat ID in telegram_alerts.py

3. **Google Gemini API Setup**:
   - Get API key from Google AI Studio
   - Update the API key in integrated_ar.py

## Usage

### Wearable Device
- **Page Navigation**: Press the physical button or use the pinch gesture to switch pages
- **Medicine Reminders**: The device shows your medication schedule and highlights when it's time to take them
- **Obstacle Detection**: 
  - When worn: Gentle beeping alerts for obstacles
  - When not worn: Aggressive beeping for obstacles
- **Health Monitoring**: Real-time heart rate and other vital signs

### Web Interface
1. Start the web server:
   ```bash
   python synapse_web.py
   ```
2. Open a browser and navigate to http://localhost:8081
3. Connect to your device from the web interface
4. Monitor vital signs and manage medicine schedules

### Telegram Alerts
1. Start the Telegram alerts system:
   ```bash
   python telegram_alerts.py
   ```
2. Use the following commands in your Telegram group:
   - `/start` - Start the bot
   - `/help` - Show help message
   - `/status` - Check monitoring status
   - `/thresholds` - View alert thresholds
   - `/startmonitoring` - Start health monitoring
   - `/stopmonitoring` - Stop health monitoring

### Computer Vision System
1. Start the integrated AR system:
   ```bash
   python integrated_ar.py
   ```
2. Use hand gestures to control the interface
3. Show medications to the camera for automatic recognition

## System Architecture
```
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│  AR Hardware  │◄────►│  Computer      │      │  Telegram     │
│  (ESP32)      │      │  Vision System │      │  Alerts       │
└───────┬───────┘      └───────┬───────┘      └───────┬───────┘
        │                      │                      │
        │                      ▼                      │
        │              ┌───────────────┐              │
        └─────────────►│  Web Interface│◄─────────────┘
                       │  (Flask)      │
                       └───────────────┘
```

## Troubleshooting

### Common Issues
1. **Serial Connection Problems**:
   - Ensure the correct port is selected
   - Check baud rate (115200)
   - Verify USB cable connection

2. **Camera Not Working**:
   - Try different camera indices (0, 1, 2, or 3)
   - Check camera permissions
   - Verify camera is connected properly

3. **ESP32 Not Responding**:
   - Try resetting the device
   - Check power supply
   - Verify serial monitor connection

4. **Telegram Alerts Not Working**:
   - Verify bot token and group chat ID
   - Ensure the bot has admin privileges in the group
   - Check internet connection

## About the Project
Synapse AR was developed as a healthcare innovation to improve patient monitoring and medication adherence. The system combines hardware and software components to create a comprehensive healthcare assistant that can be worn as glasses or used as a standalone device.

## Team Information
- **Team Name**: Synapse AR
- **Team Lead**: Pelli Sree Madhav
- **Team Members**: Ramaka Sumith Babu, Shravya Puli, Shivani Reddy Nandikonda
- **College/Organization**: Guru Nanak Institutions Technical Campus
- **Domain**: Future of Society
- **Sub Domain**: HealthTech/MedTech - Solutions for healthcare and wellness

## Contributors
- Developed by the Synapse AR team
- Contact: [Your contact information]

## License
[Your chosen license] # SynapseAR
