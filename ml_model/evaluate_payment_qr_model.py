import os
import cv2
import joblib
import numpy as np

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "ml_model",
    "payment_qr_model.pkl"
)

DATASET_DIR = os.path.join(
    BASE_DIR,
    "dataset",
    "payment_qr"
)


def extract_features(image_path):

    image = cv2.imread(
        image_path,
        cv2.IMREAD_GRAYSCALE
    )

    if image is None:
        raise ValueError(
            f"Could not read image: {image_path}"
        )

    image = cv2.resize(
        image,
        (64, 64)
    )

    image = image.astype(
        np.float32
    ) / 255.0

    mean_value = np.mean(image)
    std_value = np.std(image)
    min_value = np.min(image)
    max_value = np.max(image)

    black_ratio = np.mean(
        image < 0.5
    )

    white_ratio = np.mean(
        image >= 0.5
    )

    edges = cv2.Canny(
        (image * 255).astype(np.uint8),
        50,
        150
    )

    edge_ratio = np.mean(
        edges > 0
    )

    block_features = []

    for y in range(0, 64, 8):
        for x in range(0, 64, 8):

            block = image[
                y:y + 8,
                x:x + 8
            ]

            block_features.append(
                np.mean(block)
            )

    features = [
        mean_value,
        std_value,
        min_value,
        max_value,
        black_ratio,
        white_ratio,
        edge_ratio
    ]

    features.extend(block_features)

    return np.array(
        features,
        dtype=np.float32
    ).reshape(1, -1)


print("=" * 60)
print("PAYMENT QR MODEL EVALUATION")
print("=" * 60)

print("\nLoading payment QR model...")

model = joblib.load(MODEL_PATH)

print("Model loaded successfully.")

y_true = []
y_pred = []

class_folders = {
    "benign": 0,
    "malicious": 1
}

for folder_name, true_label in class_folders.items():

    folder_path = os.path.join(
        DATASET_DIR,
        folder_name
    )

    if not os.path.exists(folder_path):
        print(
            f"\nERROR: Folder not found: {folder_path}"
        )
        raise SystemExit(1)

    print(
        f"\nEvaluating {folder_name.upper()} images..."
    )

    image_files = [
        file for file in os.listdir(folder_path)
        if file.lower().endswith(
            (".png", ".jpg", ".jpeg", ".bmp")
        )
    ]

    print(
        f"Images found: {len(image_files)}"
    )

    for filename in image_files:

        image_path = os.path.join(
            folder_path,
            filename
        )

        try:

            features = extract_features(
                image_path
            )

            prediction = model.predict(
                features
            )[0]

            y_true.append(true_label)
            y_pred.append(int(prediction))

        except Exception as error:

            print(
                f"Skipped {filename}: {error}"
            )


if len(y_true) == 0:

    print("\nERROR: No images were evaluated.")
    raise SystemExit(1)


accuracy = accuracy_score(
    y_true,
    y_pred
)

precision = precision_score(
    y_true,
    y_pred,
    zero_division=0
)

recall = recall_score(
    y_true,
    y_pred,
    zero_division=0
)

f1 = f1_score(
    y_true,
    y_pred,
    zero_division=0
)

cm = confusion_matrix(
    y_true,
    y_pred
)


print("\n")
print("=" * 60)
print("MODEL PERFORMANCE")
print("=" * 60)

print(
    f"\nTotal Images : {len(y_true)}"
)

print(
    f"Accuracy     : {accuracy * 100:.2f}%"
)

print(
    f"Precision    : {precision * 100:.2f}%"
)

print(
    f"Recall       : {recall * 100:.2f}%"
)

print(
    f"F1-Score     : {f1 * 100:.2f}%"
)

print("\nConfusion Matrix:")
print(cm)

print("\nClassification Report:")
print(
    classification_report(
        y_true,
        y_pred,
        target_names=[
            "Benign",
            "Malicious"
        ],
        digits=4,
        zero_division=0
    )
)

print("=" * 60)
print("EVALUATION COMPLETED")
print("=" * 60)