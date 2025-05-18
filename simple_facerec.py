import face_recognition
import cv2
import numpy as np

class SimpleFacerec:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []

    def load_encoding_image(self, image_path, name):
        # Load image
        image = face_recognition.load_image_file(image_path)
        # Get face encoding
        face_encoding = face_recognition.face_encodings(image)[0]
        # Store encoding and name
        self.known_face_encodings.append(face_encoding)
        self.known_face_names.append(name)

    def detect_known_faces(self, frame):
        # Resize frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        # Convert BGR to RGB
        rgb_small_frame = small_frame[:, :, ::-1]

        # Find all faces in current frame
        face_locations = face_recognition.face_locations(rgb_small_frame)
        if not face_locations:
            return [], []

        # Get face encodings
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            # Compare face with known faces
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.6)
            name = "Unknown"

            # Use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = self.known_face_names[best_match_index]

            face_names.append(name)

        # Convert face locations back to original size
        face_locations = [(top * 4, right * 4, bottom * 4, left * 4) for (top, right, bottom, left) in face_locations]

        return face_locations, face_names 