# Re-run setup again after environment reset
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Load dataset directly from CSV
df = pd.read_csv('heart_attack_prediction_dataset.csv')

# Drop specified columns
drop_cols = [
    'Patient ID', 'Cholesterol', 'Family History', 'Exercise Hours Per Week', 'Diet',
    'Previous Heart Problems', 'Medication Use', 'Stress Level', 'Sedentary Hours Per Day',
    'Income', 'Triglycerides', 'Physical Activity Days Per Week', 'Sleep Hours Per Day',
    'Country', 'Continent', 'Hemisphere'
]
df.drop(columns=[col for col in drop_cols if col in df.columns], inplace=True)

# Engineer blood pressure features
if 'Blood Pressure' in df.columns:
    bp_split = df['Blood Pressure'].str.split('/', expand=True).astype(float)
    df['Systolic BP'] = bp_split[0]
    df['Diastolic BP'] = bp_split[1]
    df['Pulse Pressure'] = df['Systolic BP'] - df['Diastolic BP']
    df.drop(columns=['Blood Pressure'], inplace=True)

# Additional features
df['Age_BMI'] = df['Age'] * df['BMI']
df['Age_Bucket'] = pd.cut(df['Age'], bins=[0, 35, 50, 65, 100], labels=['young', 'mid', 'senior', 'elder'])
df['BMI_Category'] = pd.cut(df['BMI'], bins=[0, 18.5, 24.9, 29.9, 100], labels=['underweight', 'normal', 'overweight', 'obese'])

df.dropna(inplace=True)

# Define target and features
X = df.drop(columns=['Heart Attack Risk'])
y = df['Heart Attack Risk']

categorical_cols = X.select_dtypes(include='object').columns.tolist()
numerical_cols = X.select_dtypes(include=['int64', 'float64']).columns.tolist()

preprocessor = ColumnTransformer([
    ('num', StandardScaler(), numerical_cols),
    ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_cols)
])

X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, test_size=0.2, random_state=42)

# RandomForest pipeline
pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('classifier', RandomForestClassifier(class_weight='balanced', random_state=42))
])

# Simplified parameter grid
param_grid_simplified = {
    'classifier__n_estimators': [100],
    'classifier__max_depth': [10, 15],
    'classifier__min_samples_split': [2, 5],
    'classifier__min_samples_leaf': [1],
    'classifier__max_features': ['sqrt']
}

search_simplified = GridSearchCV(
    pipeline,
    param_grid=param_grid_simplified,
    scoring='accuracy',
    cv=5,
    n_jobs=-1,
    verbose=1
)

# Fit and evaluate
search_simplified.fit(X_train, y_train)
y_pred_simplified = search_simplified.predict(X_test)
accuracy_simplified = accuracy_score(y_test, y_pred_simplified)
report_simplified = classification_report(y_test, y_pred_simplified)

print("Best parameters:", search_simplified.best_params_)
print(f"Accuracy: {accuracy_simplified:.4f}")
print("Classification Report:")
print(report_simplified)

# Save the model to file for web app use
joblib.dump(search_simplified.best_estimator_, 'cardiac_arrest_model.pkl')
print('Model saved as cardiac_arrest_model.pkl')

