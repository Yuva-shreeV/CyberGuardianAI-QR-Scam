import joblib
import os

# Get the current folder
current_dir = os.path.dirname(os.path.abspath(__file__))

# These are the 18 features used by the final ML model
feature_names = [
    "URLLength",
    "DomainLength",
    "IsDomainIP",
    "URLSimilarityIndex",
    "CharContinuationRate",
    "TLDLegitimateProb",
    "NoOfSubDomain",
    "HasObfuscation",
    "NoOfObfuscatedChar",
    "ObfuscationRatio",
    "NoOfLettersInURL",
    "NoOfDegitsInURL",
    "DegitRatioInURL",
    "NoOfOtherSpecialCharsInURL",
    "SpacialCharRatioInURL",
    "IsHTTPS",
    "URLTitleMatchScore",
    "DomainTitleMatchScore"
]

# Save the feature names
feature_path = os.path.join(
    current_dir,
    "feature_names.pkl"
)

joblib.dump(feature_names, feature_path)

print("feature_names.pkl created successfully!")
print("Total Features:", len(feature_names))
print("\nFeatures:")

for i, feature in enumerate(feature_names):
    print(i, ":", feature)