import argparse
import json
import random
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import (
    accuracy_score, confusion_matrix, f1_score, precision_score,
    recall_score, roc_auc_score, roc_curve,
)
from tensorflow import keras
from tensorflow.keras import layers


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--student_id", default="unknown")
    parser.add_argument("--group_id", default="unknown")
    parser.add_argument("--image_size", type=int, default=128)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--learning_rate", type=float, default=0.001)
    parser.add_argument("--dropout_rate", type=float, default=0.3)
    parser.add_argument("--conv_filters", type=int, nargs=3, default=[16, 32, 64])
    parser.add_argument("--dense_units", type=int, default=32)
    parser.add_argument("--patience", type=int, default=3)
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()

    if min(args.epochs, args.image_size, args.batch_size, args.dense_units, args.patience) <= 0:
        parser.error("epochs, image_size, batch_size, dense_units, patience는 1 이상이어야 합니다.")
    if any(value <= 0 for value in args.conv_filters):
        parser.error("conv_filters의 세 값은 모두 1 이상이어야 합니다.")
    if not 0 <= args.dropout_rate < 1:
        parser.error("dropout_rate는 0 이상 1 미만이어야 합니다.")
    if not 0 < args.learning_rate:
        parser.error("learning_rate는 0보다 커야 합니다.")
    if not 0 <= args.threshold <= 1:
        parser.error("threshold는 0 이상 1 이하여야 합니다.")
    return args


def resolve_data_root(received: Path) -> Path:
    candidates = [received, received / "data" / "resized", received / "resized"]
    for candidate in candidates:
        if all((candidate / item).is_dir() for item in [
            "학습/정상", "학습/불량", "테스트/정상", "테스트/불량"
        ]):
            return candidate
    raise FileNotFoundError(f"학습/테스트 정상·불량 폴더를 찾지 못했습니다: {received}")


args = parse_args()
seed = 42
random.seed(seed)
np.random.seed(seed)
tf.random.set_seed(seed)

print("TensorFlow:", tf.__version__)
print("GPU devices:", tf.config.list_physical_devices("GPU"))
if not tf.config.list_physical_devices("GPU"):
    raise RuntimeError("TensorFlow GPU를 찾지 못했습니다.")

data_root = resolve_data_root(Path(args.data_dir))
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)
train_dir, test_dir = data_root / "학습", data_root / "테스트"
class_names = ["불량", "정상"]  # Keras 라벨: 불량=0, 정상=1
image_size = args.image_size
batch_size = args.batch_size
validation_split = 0.2
conv_filters = tuple(args.conv_filters)

print("Experiment config:", json.dumps({
    "epochs": args.epochs,
    "image_size": image_size,
    "batch_size": batch_size,
    "learning_rate": args.learning_rate,
    "dropout_rate": args.dropout_rate,
    "conv_filters": conv_filters,
    "dense_units": args.dense_units,
    "patience": args.patience,
    "threshold": args.threshold,
}, ensure_ascii=False))

def count_images(folder: Path) -> int:
    return sum(1 for p in folder.rglob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp"})

train_defect = count_images(train_dir / "불량")
train_normal = count_images(train_dir / "정상")
if min(train_defect, train_normal) == 0:
    raise ValueError("학습 정상 또는 불량 이미지가 없습니다.")
total = train_defect + train_normal
class_weight = {0: total / (2 * train_defect), 1: total / (2 * train_normal)}

common = dict(
    class_names=class_names, image_size=(image_size, image_size),
    batch_size=batch_size, color_mode="rgb", label_mode="binary",
)
train_ds = keras.utils.image_dataset_from_directory(
    train_dir, validation_split=validation_split, subset="training", seed=seed, **common
)
val_ds = keras.utils.image_dataset_from_directory(
    train_dir, validation_split=validation_split, subset="validation", seed=seed, **common
)
test_ds = keras.utils.image_dataset_from_directory(
    test_dir, shuffle=False, **common
)
test_paths = [Path(p) for p in test_ds.file_paths]
autotune = tf.data.AUTOTUNE
train_ds, val_ds, test_ds = (
    train_ds.prefetch(autotune), val_ds.prefetch(autotune), test_ds.prefetch(autotune)
)

model = keras.Sequential([
    layers.Input(shape=(image_size, image_size, 3)),
    layers.Rescaling(1.0 / 255),
    layers.Conv2D(conv_filters[0], 3, activation="relu"), layers.MaxPooling2D(),
    layers.Conv2D(conv_filters[1], 3, activation="relu"), layers.MaxPooling2D(),
    layers.Conv2D(conv_filters[2], 3, activation="relu"), layers.MaxPooling2D(),
    layers.Flatten(), layers.Dropout(args.dropout_rate),
    layers.Dense(args.dense_units, activation="relu"), layers.Dense(1, activation="sigmoid"),
])
model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=args.learning_rate),
    loss="binary_crossentropy", metrics=["accuracy"],
)
early_stop = keras.callbacks.EarlyStopping(
    monitor="val_loss", patience=args.patience, restore_best_weights=True
)

mlflow.log_params({
    "student_id": args.student_id, "group_id": args.group_id,
    "epochs_requested": args.epochs, "image_size": image_size,
    "batch_size": batch_size, "train_normal": train_normal,
    "train_defect": train_defect,
    "learning_rate": args.learning_rate,
    "dropout_rate": args.dropout_rate,
    "conv_filters": "-".join(map(str, conv_filters)),
    "dense_units": args.dense_units,
    "patience": args.patience,
    "threshold": args.threshold,
})
history = model.fit(
    train_ds, validation_data=val_ds, epochs=args.epochs,
    class_weight=class_weight, callbacks=[early_stop], verbose=2,
)
history_df = pd.DataFrame(history.history)
history_df.index = history_df.index + 1
history_df.index.name = "epoch"
history_df.to_csv(output_dir / "training_history.csv", encoding="utf-8-sig")
for epoch, row in history_df.iterrows():
    mlflow.log_metrics({k: float(v) for k, v in row.items()}, step=int(epoch))

true_normal = np.concatenate([y.numpy().reshape(-1) for _, y in test_ds]).astype(int)
normal_prob = model.predict(test_ds, verbose=0).reshape(-1)
y_true = 1 - true_normal
defect_prob = 1 - normal_prob
threshold = args.threshold
y_pred = (defect_prob >= threshold).astype(int)
metrics = {
    "accuracy": accuracy_score(y_true, y_pred),
    "defect_precision": precision_score(y_true, y_pred, zero_division=0),
    "defect_recall": recall_score(y_true, y_pred, zero_division=0),
    "defect_f1": f1_score(y_true, y_pred, zero_division=0),
    "roc_auc": roc_auc_score(y_true, defect_prob),
}
mlflow.log_metrics({k: float(v) for k, v in metrics.items()})
pd.DataFrame({"metric": metrics.keys(), "value": metrics.values()}).to_csv(
    output_dir / "evaluation_summary.csv", index=False, encoding="utf-8-sig"
)
pd.DataFrame({
    "file_path": [str(p) for p in test_paths],
    "file_name": [p.name for p in test_paths],
    "true_label": np.where(y_true == 1, "defect", "normal"),
    "defect_probability": defect_prob,
    "predicted_label": np.where(y_pred == 1, "defect", "normal"),
    "is_correct": y_true == y_pred,
}).to_csv(output_dir / "test_predictions.csv", index=False, encoding="utf-8-sig")

history_df[["loss", "val_loss", "accuracy", "val_accuracy"]].plot(
    subplots=True, layout=(2, 2), figsize=(10, 7), grid=True
)
plt.tight_layout(); plt.savefig(output_dir / "training_curves.png", dpi=150); plt.close()
cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
fig, ax = plt.subplots(figsize=(5, 4))
image = ax.imshow(cm, cmap="Blues")
fig.colorbar(image, ax=ax)
ax.set(
    xticks=[0, 1], yticks=[0, 1],
    xticklabels=["normal", "defect"], yticklabels=["normal", "defect"],
    xlabel="Predicted", ylabel="Actual", title="Confusion Matrix",
)
text_threshold = cm.max() / 2 if cm.size else 0
for row in range(cm.shape[0]):
    for col in range(cm.shape[1]):
        ax.text(
            col, row, str(cm[row, col]), ha="center", va="center",
            color="white" if cm[row, col] > text_threshold else "black",
        )
plt.tight_layout()
plt.savefig(output_dir / "confusion_matrix.png", dpi=150); plt.close()
fpr, tpr, _ = roc_curve(y_true, defect_prob)
plt.plot(fpr, tpr, label=f"AUC={metrics['roc_auc']:.3f}")
plt.plot([0, 1], [0, 1], "--"); plt.legend(); plt.xlabel("FPR"); plt.ylabel("TPR")
plt.tight_layout(); plt.savefig(output_dir / "roc_curve.png", dpi=150); plt.close()

model.save(output_dir / "chromate_cnn.keras")
summary = {
    "student_id": args.student_id, "group_id": args.group_id,
    "gpu": [d.name for d in tf.config.list_physical_devices("GPU")],
    "epochs_completed": len(history_df), "threshold": threshold,
    "class_order": {"0": "defect", "1": "normal"},
    "experiment": {
        "image_size": image_size,
        "batch_size": batch_size,
        "learning_rate": args.learning_rate,
        "dropout_rate": args.dropout_rate,
        "conv_filters": conv_filters,
        "dense_units": args.dense_units,
        "patience": args.patience,
    },
    **{k: float(v) for k, v in metrics.items()},
}
(output_dir / "run_summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("RESULT_SUMMARY=", json.dumps(summary, ensure_ascii=False))
