import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Load dataset
data = pd.read_csv("Hypertension-risk-model-main.csv")

# Keep only relevant columns
keep_columns = ['age', 'male', 'sysBP', 'diaBP', 'heartRate', 'Risk']
data = data[keep_columns]

# Handle missing values (drop rows with any missing)
data = data.dropna()

# Features and target
X = data.drop(columns=['Risk'])
y = data['Risk']

# Split into train/test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Random Forest model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
print(f'Accuracy: {accuracy:.4f}')
print('Classification Report:')
print(classification_report(y_test, predictions))

# Save model to file for web app use
joblib.dump(model, 'sensor_rf_model.pkl')
print('Model saved as sensor_rf_model.pkl')
