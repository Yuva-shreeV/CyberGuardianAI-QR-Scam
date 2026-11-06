import pandas as pd
import os

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression

from xgboost import XGBClassifier

# -----------------------------
# Load Dataset
# -----------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(current_dir, "..", "dataset", "PhiUSIIL_Phishing_URL_Dataset.csv")

data = pd.read_csv(dataset_path)

# Remove text columns
data = data.drop(columns=["URL", "Domain", "TLD", "Title"])

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

# Models
models = {
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
    "Decision Tree": DecisionTreeClassifier(random_state=42),
    "Logistic Regression": LogisticRegression(max_iter=1000),
    "XGBoost": XGBClassifier(
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=42
    )
}

print("=" * 60)
print("MODEL COMPARISON")
print("=" * 60)

results = []

for name, model in models.items():

    print(f"\nTraining {name}...")

    model.fit(X_train, y_train)

    prediction = model.predict(X_test)

    accuracy = accuracy_score(y_test, prediction)

    results.append([name, accuracy])

    print(f"{name} Accuracy : {accuracy*100:.2f}%")

print("\n" + "=" * 60)
print("FINAL RESULTS")
print("=" * 60)

results = pd.DataFrame(results, columns=["Model", "Accuracy"])

print(results.sort_values(by="Accuracy", ascending=False))