import pandas as pd
import joblib
import shap
import os

# ------------------------------------------------
# Load model and feature names
# ------------------------------------------------

current_dir = os.path.dirname(os.path.abspath(__file__))

model = joblib.load(os.path.join(current_dir, "model.pkl"))
feature_names = joblib.load(os.path.join(current_dir, "feature_names.pkl"))

# ------------------------------------------------
# Load dataset
# ------------------------------------------------

dataset_path = os.path.join(
    current_dir,
    "..",
    "dataset",
    "PhiUSIIL_Phishing_URL_Dataset.csv"
)

data = pd.read_csv(dataset_path)

# Keep only selected features
X = data[feature_names]

# Select one sample
sample = X.iloc[[0]]

# ------------------------------------------------
# Prediction
# ------------------------------------------------

prediction = model.predict(sample)[0]
probability = model.predict_proba(sample)[0]

print("=" * 50)

print("Prediction :", "Safe" if prediction == 1 else "Phishing")

print("Confidence :", round(max(probability) * 100, 2), "%")

print("=" * 50)

# ------------------------------------------------
# SHAP Explanation
# ------------------------------------------------

explainer = shap.TreeExplainer(model)

shap_values = explainer.shap_values(sample)

print("\nTop Feature Contributions\n")

if isinstance(shap_values, list):
    values = shap_values[1][0]
else:
    values = shap_values[0]

importance = pd.DataFrame({
    "Feature": feature_names,
    "Contribution": values
})

importance["Abs"] = importance["Contribution"].abs()

importance = importance.sort_values(
    by="Abs",
    ascending=False
)

print(importance[["Feature", "Contribution"]].head(10))