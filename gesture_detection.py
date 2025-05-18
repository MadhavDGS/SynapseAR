import cv2
import mediapipe as mp
import math
import serial
import numpy as np
import time
import serial.tools.list_ports
import sys
import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser(description='AR Gesture Control')
parser.add_argument('--port', help='Specify serial port (e.g., /dev/tty.usbmodem14201)')
args = parser.parse_args()

# List all available ports
ports = list(serial.tools.list_ports.comports())
print("Available ports:")
for port in ports:
    print(port.device)

# Try to find Arduino port
arduino_port = None
if args.port:
    arduino_port = args.port
    print(f"Using specified port: {arduino_port}")
else:
    for port in ports:
        if 'usbmodem' in port.device.lower() or 'usbserial' in port.device.lower():
            arduino_port = port.device
            break

if arduino_port is None:
    print("No Arduino port found!")
    exit()

print(f"Using Arduino port: {arduino_port}")

# Initialize Arduino serial connection with 115200 baud rate
try:
    arduino = serial.Serial(arduino_port, 115200, timeout=1)  # Changed to 115200
    time.sleep(2)  # Wait for Arduino to reset
    print("Arduino connected successfully!")
    
    # Flush any existing data
    arduino.reset_input_buffer()
    arduino.reset_output_buffer()
    
    # Send test command
    arduino.write(b'test\n')
    arduino.flush()
    
    # Read response with error handling
    try:
        response = arduino.readline()
        if response:
            try:
                decoded_response = response.decode('utf-8', errors='replace').strip()
                print(f"Arduino response: {decoded_response}")
            except UnicodeDecodeError:
                print("Received binary response from Arduino")
    except Exception as e:
        print(f"Error reading from Arduino: {e}")
    
except Exception as e:
    print(f"Failed to connect to Arduino: {e}")
    exit()

# Mediapipe drawing and hand detection setup
mp_drawing = mp.solutions.drawing_utils
hand_mpDraw = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# Track current page (0-5)
current_page = 0
MAX_PAGES = 6

# Function to send page switch signal
def switch_page():
    global current_page
    print("Switching page!")  # Debug print
    try:
        # Send button press command with newline
        cmd = "button_press\n"
        print(f"Sending command: {cmd.strip()}")
        arduino.write(cmd.encode())
        arduino.flush()
        
        # Read responses until we get CMD_END
        while True:
            try:
                response = arduino.readline()
                if not response:
                    break
                    
                try:
                    decoded_response = response.decode('utf-8', errors='replace').strip()
                    print(f"Arduino response: {decoded_response}")
                    
                    # Check for successful page change
                    if "Page changed successfully" in decoded_response:
                        current_page = (current_page + 1) % MAX_PAGES
                        print(f"Updated page counter to: {current_page}")
                    
                    # Break the loop when we see CMD_END
                    if decoded_response == "CMD_END":
                        break
                        
                except UnicodeDecodeError:
                    print("Received binary response from Arduino")
                    
            except Exception as e:
                print(f"Error reading from Arduino: {e}")
                break
        
        # Wait for a moment to ensure command is processed
        time.sleep(0.1)
        
    except Exception as e:
        print(f"Error sending button press command: {e}")

# Function to draw a dotted line
def drawline(img, pt1, pt2, color, thickness=1, style='dotted', gap=20):
    dist = ((pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2) ** .5
    pts = []
    for i in np.arange(0, dist, gap):
        r = i / dist
        x = int((pt1[0] * (1 - r) + pt2[0] * r) + .5)
        y = int((pt1[1] * (1 - r) + pt2[1] * r) + .5)
        p = (x, y)
        pts.append(p)
    if style == 'dotted':
        for p in pts:
            cv2.circle(img, p, thickness, color, -1)
    else:
        s = pts[0]
        e = pts[0]
        i = 0
        for p in pts:
            s = e
            e = p
            if i % 2 == 1:
                cv2.line(img, s, e, color, thickness)
            i += 1

# Function to draw page indicators
def draw_page_indicators(img, current_page, max_pages):
    start_x = 10
    y = 70
    circle_radius = 10
    spacing = 30
    
    for i in range(max_pages):
        center = (start_x + i * spacing, y)
        if i == current_page:
            cv2.circle(img, center, circle_radius, (0, 255, 0), -1)  # Filled circle for current page
        else:
            cv2.circle(img, center, circle_radius, (128, 128, 128), 2)  # Empty circle for other pages

# Try multiple camera indices
camera_index = 3
cap = None
for index in [3]:
    cap = cv2.VideoCapture(index)
    if cap.isOpened():
        camera_index = index
        print(f"Successfully opened camera at index {index}")
        break
    else:
        print(f"Failed to open camera at index {index}")

if not cap or not cap.isOpened():
    print("Could not open any camera. Please check your camera connection.")
    arduino.close()
    exit()

distance = -1
last_switch_time = 0  # For debouncing

with mp_hands.Hands(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        max_num_hands=2) as hands:  # Enable detection of up to 2 hands
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Failed to read from camera")
            continue
        image = cv2.flip(image, 1)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = hands.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Draw instructions and page indicators
        cv2.putText(image, "Join index finger and thumb to switch pages", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        draw_page_indicators(image, current_page, MAX_PAGES)
        cv2.putText(image, f"Current Page: {current_page}", (10, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                lmList = []
                for id, lm in enumerate(hand_landmarks.landmark):
                    h, w, c = image.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lmList.append([id, cx, cy])
                    tips = [0, 4, 8, 12, 16, 20]
                    if id in tips:
                        cv2.circle(image, (cx, cy), 15, (0, 255, 0), cv2.FILLED)

                # Calculate distance between index and thumb
                if len(lmList) > 8:  # Make sure index and thumb landmarks exist
                    distance = math.hypot(lmList[8][1] - lmList[4][1], lmList[8][2] - lmList[4][2])
                    
                    # Check if fingers are close enough to trigger page switch
                    current_time = time.time()
                    if distance < 50 and (current_time - last_switch_time) > 1.0:  # Increased threshold to 50
                        print(f"Fingers close! Distance: {distance}")  # Debug print
                        switch_page()
                        last_switch_time = current_time

                    # Draw line between index and thumb
                    drawline(image, (lmList[4][1], lmList[4][2]), (lmList[8][1], lmList[8][2]), (0, 0, 255),
                            thickness=1, style='dotted', gap=10)
                    
                    # Add distance text to screen
                    cv2.putText(image, f"Distance: {int(distance)}", (10, 150),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Draw landmarks
                mp_drawing.draw_landmarks(
                    image, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                    landmark_drawing_spec=hand_mpDraw.DrawingSpec(color=(0, 255, 0)),
                    connection_drawing_spec=hand_mpDraw.DrawingSpec(color=(255, 0, 0)))

        cv2.imshow('AR Page Controller', image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Release resources
cap.release()
cv2.destroyAllWindows()
arduino.close()  # Close the serial connection
