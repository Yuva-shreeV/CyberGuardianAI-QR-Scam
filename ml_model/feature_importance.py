import pandas as pd
import os
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# -----------------------------
# Load Dataset
# -----------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(current_dir, "..", "dataset", "PhiUSIIL_Phishing_URL_Dataset.csv")

data = pd.read_csv(dataset_path)

# Remove text columns
data = data.drop(columns=["URL", "Domain", "TLD", "Title"])

# Features and Label
X = data.drop("label", axis=1)
y = data["label"]

# Train-Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

# Train Random Forest
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

# Feature Importance
importance = model.feature_importances_

feature_importance = pd.DataFrame({
    "Feature": X.columns,
    "Importance": importance
})

feature_importance = feature_importance.sort_values(
    by="Importance",
    ascending=False
)

print("\nTop 20 Important Features\n")
print(feature_importance.head(20))

# Plot
plt.figure(figsize=(10,8))
plt.barh(
    feature_importance["Feature"][:20],
    feature_importance["Importance"][:20]
)

plt.gca().invert_yaxis()
plt.title("Top 20 Feature Importance")
plt.xlabel("Importance")
plt.tight_layout()
plt.show()