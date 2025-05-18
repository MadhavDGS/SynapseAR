import cv2
import os
from simple_facerec import SimpleFacerec

# Initialize the face recognition system
sfr = SimpleFacerec()

# Load images from the face_images folder
face_images_dir = "face_images"
print("Loading known faces...")
for filename in os.listdir(face_images_dir):
    if filename.endswith((".jpg", ".jpeg", ".png")):
        # Get the name from the filename (remove extension)
        name = os.path.splitext(filename)[0]
        # Load the image
        image_path = os.path.join(face_images_dir, filename)
        try:
            sfr.load_encoding_image(image_path, name)
            print(f"Loaded {name}'s face")
        except Exception as e:
            print(f"Error loading {name}'s face: {str(e)}")

print("Starting video capture...")
# Load Camera
cap = cv2.VideoCapture(2)  # Try camera index 0 first

# Set a lower resolution for smoother video
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Check if camera opened successfully
if not cap.isOpened():
    print("Error: Could not open camera. Trying camera index 1...")
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("Error: Could not open camera. Trying camera index 2...")
        cap = cv2.VideoCapture(2)
        if not cap.isOpened():
            print("Error: Could not open any camera.")
            exit()

print("Camera opened successfully. Press 'q' to quit.")

frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        continue

    # Process every 2nd frame to reduce load
    frame_count += 1
    if frame_count % 2 != 0:
        continue

    try:
        # Detect Faces
        face_locations, face_names = sfr.detect_known_faces(frame)
    except Exception as e:
        face_locations, face_names = [], []

    # Only draw boxes for detected faces
    if not face_locations:
        print("No faces detected")

    for face_loc, name in zip(face_locations, face_names):
        y1, x2, y2, x1 = face_loc[0], face_loc[1], face_loc[2], face_loc[3]

        # Draw rectangle and name
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 200), 4)
        cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 200), 2)
        print(f"Detected face: {name}")

    cv2.imshow("Frame", frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()