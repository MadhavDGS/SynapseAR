# Install first if needed:
# pip install imbalanced-learn openpyxl

import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from imblearn.over_sampling import SMOTE
import joblib
import os

# Check if file exists
excel_path = "/Users/sreemadhav/SreeMadhav/AI/google teachable machine/Testing Data.xlsx"
if not os.path.exists(excel_path):
    print(f"Error: File not found: {excel_path}")
    print("Using dummy data instead for demonstration purposes")
    
    # Create dummy data
    import numpy as np
    np.random.seed(42)
    n_samples = 100
    
    # Create synthetic features
    features = {
        'Age': np.random.randint(5, 18, n_samples),
        'Number of Siblings': np.random.randint(0, 5, n_samples),
        'Number of Bio. Parents': np.random.randint(0, 2, n_samples),
        'Poverty Status': np.random.randint(0, 2, n_samples),
        'Number of Impairments': np.random.randint(0, 3, n_samples),
        'Number of Type A Stressors': np.random.randint(0, 5, n_samples),
        'Number of Type B Stressors': np.random.randint(0, 5, n_samples),
        'Frequency Temper Tantrums': np.random.randint(0, 5, n_samples),
        'Frequency Irritable Mood': np.random.randint(0, 5, n_samples),
        'Number of Sleep Disturbances': np.random.randint(0, 3, n_samples),
        'Number of Physical Symptoms': np.random.randint(0, 5, n_samples),
        'Number of Sensory Sensitivities': np.random.randint(0, 3, n_samples),
        'Family History - Substance Abuse': np.random.randint(0, 2, n_samples),
        'Family History - Psychiatric Diagnosis': np.random.randint(0, 2, n_samples)
    }
    
    # Create target with class imbalance (20% positive)
    target = np.random.choice([0, 1], size=n_samples, p=[0.8, 0.2])
    
    # Create DataFrame
    df = pd.DataFrame(features)
    df['GAD'] = target
else:
    # Load dataset from Excel
    df = pd.read_excel(excel_path)

# Select features and target
X = df[[
    'Age', 'Number of Siblings', 'Number of Bio. Parents',
    'Poverty Status', 'Number of Impairments',
    'Number of Type A Stressors', 'Number of Type B Stressors',
    'Frequency Temper Tantrums', 'Frequency Irritable Mood',
    'Number of Sleep Disturbances', 'Number of Physical Symptoms',
    'Number of Sensory Sensitivities',
    'Family History - Substance Abuse',
    'Family History - Psychiatric Diagnosis'
]]
y = df['GAD']

# Handle missing values
imputer = SimpleImputer(strategy='mean')
X_imputed = imputer.fit_transform(X)

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X_imputed, y, test_size=0.2, stratify=y, random_state=42
)

# Apply SMOTE to training data
smote = SMOTE(random_state=42)
X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

# Random Forest + hyperparameter tuning
param_grid = {
    'n_estimators': [100, 300],
    'max_depth': [10, 20, None],
    'min_samples_split': [2, 5],
    'min_samples_leaf': [1, 2],
    'bootstrap': [True]
}
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
grid_search = GridSearchCV(
    RandomForestClassifier(random_state=42),
    param_grid, cv=cv, n_jobs=-1
)
grid_search.fit(X_resampled, y_resampled)

# Evaluate model
model = grid_search.best_estimator_
y_pred = model.predict(X_test)

print(f"Model Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")
print("Classification Report:")
print(classification_report(y_test, y_pred))
print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# Save model and imputer for web app
joblib.dump(model, 'anxiety_model.pkl')
joblib.dump(imputer, 'anxiety_imputer.pkl')
print("Models saved as anxiety_model.pkl and anxiety_imputer.pkl")
