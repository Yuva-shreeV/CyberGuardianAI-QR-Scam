import pandas as pd
import os

# Get the current folder
current_dir = os.path.dirname(os.path.abspath(__file__))

# Dataset path
dataset_path = os.path.join(current_dir, "..", "dataset", "PhiUSIIL_Phishing_URL_Dataset.csv")

# Read dataset
data = pd.read_csv(dataset_path)

# -----------------------------
# Basic Information
# -----------------------------
print("=" * 60)
print("DATASET INFORMATION")
print("=" * 60)

print("\nDataset Shape:")
print(data.shape)

print("\nColumn Names:")
print(data.columns.tolist())

print("\nData Types:")
print(data.dtypes)

# -----------------------------
# Missing Values
# -----------------------------
print("\n" + "=" * 60)
print("MISSING VALUES")
print("=" * 60)

print(data.isnull().sum())

# -----------------------------
# Duplicate Rows
# -----------------------------
print("\n" + "=" * 60)
print("DUPLICATE ROWS")
print("=" * 60)

print("Duplicate Rows:", data.duplicated().sum())

# -----------------------------
# Label Distribution
# -----------------------------
print("\n" + "=" * 60)
print("LABEL DISTRIBUTION")
print("=" * 60)

print(data["label"].value_counts())