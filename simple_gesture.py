import cv2
import numpy as np
import serial
import serial.tools.list_ports
import time
import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Simple AR Gesture Control')
parser.add_argument('--port', help='Specify serial port (e.g., /dev/tty.usbmodem14201)')
args = parser.parse_args()

# List all available ports
ports = list(serial.tools.list_ports.comports())
print("Available ports:")
for port in ports:
    print(f"  {port.device} - {port.description}")

# Try to find Arduino port
arduino_port = None
if args.port:
    arduino_port = args.port
    print(f"Using specified port: {arduino_port}")
else:
    for port in ports:
        if 'usbmodem' in port.device.lower() or 'usbserial' in port.device.lower() or 'FTDI' in port.description:
            arduino_port = port.device
            print(f"Auto-detected port: {arduino_port} - {port.description}")
            break

if arduino_port is None:
    print("No Arduino port found! Please specify a port using --port argument.")
    exit()

# Initialize Arduino serial connection
try:
    arduino = serial.Serial(arduino_port, 115200, timeout=1)
    time.sleep(2)  # Wait for Arduino to reset
    print("Arduino connected successfully!")
    
    # Flush any existing data
    arduino.reset_input_buffer()
    arduino.reset_output_buffer()
    
    # Send test command
    arduino.write(b'ping\n')
    arduino.flush()
    
    # Read response
    response = arduino.readline().decode('utf-8', errors='replace').strip()
    print(f"Arduino response: {response}")
    
except Exception as e:
    print(f"Failed to connect to Arduino: {e}")
    exit()

# Track current page (0-5)
current_page = 0
MAX_PAGES = 6

def switch_page():
    """Send page switch command to Arduino"""
    global current_page
    print("Switching page!")
    try:
        cmd = "button_press\n"
        arduino.write(cmd.encode())
        arduino.flush()
        
        # Read responses until we get CMD_END
        start_time = time.time()
        while (time.time() - start_time) < 3:  # Timeout after 3 seconds
            response = arduino.readline().decode('utf-8', errors='replace').strip()
            print(f"Response: {response}")
            
            if "Page changed successfully" in response:
                current_page = (current_page + 1) % MAX_PAGES
                print(f"Updated page counter to: {current_page}")
            
            if "CMD_END" in response:
                break
                
        time.sleep(0.1)  # Small delay
        
    except Exception as e:
        print(f"Error sending command: {e}")

# Function to draw a dotted line (copied from gesture_detection.py)
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

def draw_page_indicators(img, current_page, max_pages):
    """Draw page indicator circles"""
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

# Function to draw hand landmarks similar to mediapipe
def draw_hand_landmarks(img, contour, center):
    if contour is None or len(contour) < 5:
        return
    
    # Get contour's bounding box
    x, y, w, h = cv2.boundingRect(contour)
    
    # If contour is too small, don't try to draw landmarks
    if w < 30 or h < 30:
        return
    
    # Draw main hand contour in green
    cv2.drawContours(img, [contour], -1, (0, 255, 0), 2)
    
    # Draw center point of contour (similar to palm center)
    cv2.circle(img, center, 7, (255, 0, 0), -1)
    
    # We'll add some artificial fingertip points to make it look similar to mediapipe
    # For simplicity, we'll estimate these based on the bounding box
    
    # Approximate polygon for the contour to find potential fingertips
    epsilon = 0.02 * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True)
    
    # Get convex hull and convexity defects to find finger-like structures
    hull = cv2.convexHull(contour, returnPoints=False)
    
    # Only proceed if we have enough points for hull
    if len(hull) > 3:
        try:
            defects = cv2.convexityDefects(contour, hull)
            if defects is not None:
                # We'll use the convexity defects to estimate fingertips
                finger_points = []
                
                for i in range(defects.shape[0]):
                    s, e, f, d = defects[i, 0]
                    start = tuple(contour[s][0])
                    end = tuple(contour[e][0])
                    far = tuple(contour[f][0])
                    
                    # Add start and end points which might be fingertips
                    finger_points.append(start)
                    finger_points.append(end)
                    
                    # Draw defect point (between fingers) in red
                    cv2.circle(img, far, 5, (0, 0, 255), -1)
                
                # Draw potential fingertips in green circles
                for point in finger_points:
                    cv2.circle(img, point, 15, (0, 255, 0), cv2.FILLED)
                
                # If we have at least two points, draw connections like in the mediapipe version
                if len(finger_points) >= 2:
                    # Draw a dotted line between the first two points (like thumb and index)
                    pt1 = finger_points[0]
                    pt2 = finger_points[1]
                    drawline(img, pt1, pt2, (0, 0, 255), thickness=1, style='dotted', gap=10)
                    
                    # Calculate distance between these points - similar to the original
                    distance = np.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)
                    cv2.putText(img, f"Distance: {int(distance)}", (10, 150),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Return the distance for pinch detection
                    return distance, pt1, pt2
        except:
            pass
    
    return None, None, None

# Try to open camera
camera_index = 2
cap = None
for index in [2]:
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

# Create a window with trackbars for HSV color thresholding
cv2.namedWindow('HSV Controls')
cv2.createTrackbar('Hue Min', 'HSV Controls', 0, 179, lambda x: None)
cv2.createTrackbar('Hue Max', 'HSV Controls', 179, 179, lambda x: None)
cv2.createTrackbar('Sat Min', 'HSV Controls', 50, 255, lambda x: None)
cv2.createTrackbar('Sat Max', 'HSV Controls', 255, 255, lambda x: None)
cv2.createTrackbar('Val Min', 'HSV Controls', 50, 255, lambda x: None)
cv2.createTrackbar('Val Max', 'HSV Controls', 255, 255, lambda x: None)

# Initialize some default skin color HSV values (can be adjusted with trackbars)
# Default values for skin tone detection
cv2.setTrackbarPos('Hue Min', 'HSV Controls', 0)
cv2.setTrackbarPos('Hue Max', 'HSV Controls', 20)
cv2.setTrackbarPos('Sat Min', 'HSV Controls', 40)
cv2.setTrackbarPos('Sat Max', 'HSV Controls', 170)
cv2.setTrackbarPos('Val Min', 'HSV Controls', 100)
cv2.setTrackbarPos('Val Max', 'HSV Controls', 255)

# Variables for gesture detection
last_gesture_time = 0
min_gesture_interval = 1.0  # Minimum seconds between gestures
previous_contour_area = 0
contour_change_threshold = 5000  # Threshold for detecting significant changes
last_pinch_time = 0  # For debouncing pinch gestures

print("\nGesture Control Instructions:")
print("1. Adjust the HSV sliders to detect your hand (skin color)")
print("2. Move your fingers to create a pinching motion")
print("3. Press 'q' to quit")

while True:
    # Read frame from camera
    success, frame = cap.read()
    if not success:
        print("Failed to read from camera")
        break
        
    # Flip the frame horizontally for a more intuitive mirror view
    frame = cv2.flip(frame, 1)
    
    # Get current positions of trackbars
    h_min = cv2.getTrackbarPos('Hue Min', 'HSV Controls')
    h_max = cv2.getTrackbarPos('Hue Max', 'HSV Controls')
    s_min = cv2.getTrackbarPos('Sat Min', 'HSV Controls')
    s_max = cv2.getTrackbarPos('Sat Max', 'HSV Controls')
    v_min = cv2.getTrackbarPos('Val Min', 'HSV Controls')
    v_max = cv2.getTrackbarPos('Val Max', 'HSV Controls')
    
    # Convert to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Create mask for skin color detection
    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])
    mask = cv2.inRange(hsv, lower, upper)
    
    # Apply some morphological operations to clean up the mask
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=2)
    
    # Find contours in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Draw instructions text (same as original gesture_detection.py)
    cv2.putText(frame, "Join index finger and thumb to switch pages", (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Draw page indicators
    draw_page_indicators(frame, current_page, MAX_PAGES)
    cv2.putText(frame, f"Current Page: {current_page}", (10, 100),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Find the largest contour (assuming it's the hand)
    largest_contour = None
    largest_area = 0
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > largest_area and area > 1000:  # Minimum size to avoid noise
            largest_area = area
            largest_contour = contour
    
    # Process the hand contour if found
    if largest_contour is not None:
        # Calculate center of the contour
        M = cv2.moments(largest_contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            center = (cx, cy)
            
            # Draw hand landmarks
            distance, pt1, pt2 = draw_hand_landmarks(frame, largest_contour, center)
            
            # Check for pinch gesture
            current_time = time.time()
            if distance is not None and distance < 50 and current_time - last_pinch_time > 1.0:
                print(f"Pinch detected! Distance: {distance}")
                cv2.putText(frame, "PINCH DETECTED!", (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                # Switch page on Arduino
                switch_page()
                last_pinch_time = current_time
            
            # Show contour area for debugging
            cv2.putText(frame, f"Area: {int(largest_area)}", (cx-50, cy-20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    # Show the results
    cv2.imshow('Hand Gesture Control', frame)
    cv2.imshow('Mask', mask)
    
    # Check for key press to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up
cap.release()
cv2.destroyAllWindows()
arduino.close()
print("Gesture control ended") 