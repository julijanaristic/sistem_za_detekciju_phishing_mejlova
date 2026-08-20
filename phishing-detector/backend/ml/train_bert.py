from pathlib import Path 

import numpy as np 
import torch 
from torch.utils.data import Dataset 
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    roc_auc_score,
    confusion_matrix,
)
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
)

from split_utils import get_train_test_split

BASE_DIR = Path(__file__).resolve().parent 
MODEL_DIR = BASE_DIR / "saved_models" / "bert"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "distilbert-base-uncased"
MAX_LENGTH = 256
NUM_EPOCHS = 2
BATCH_SIZE = 16
LEARNING_RATE = 2e-5

MAX_TRAIN_SAMPLES: int | None = None 
MAX_TEST_SAMPLES: int | None = None 

class EmailDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length):
        self.encodings = tokenizer(
            list(texts),
            truncation=True,
            padding=True,
            max_length=max_length,
        )
        self.labels = list(labels)
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item 
    
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    probs = torch.softmax(torch.tensor(logits), dim=1)[:, 1].numpy()
    preds = np.argmax(logits, axis=1)

    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average="binary", zero_division=0
    )
    acc = accuracy_score(labels, preds)
    try:
        auc = roc_auc_score(labels, probs)
    except ValueError:
        auc = float("nan")
    
    return {
        "accuracy": acc,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": auc,
    }

def main():
    print("Loading dataset and building train/test split (same as baseline...)")
    train_df, test_df, has_source = get_train_test_split()

    if MAX_TRAIN_SAMPLES:
        train_df = train_df.sample(
            n=min(MAX_TRAIN_SAMPLES, len(train_df)), random_state=42
        ).reset_index(drop=True)
        print(f"[INFO] Subsampled train set to {len(train_df)} rows for a fast run.")
    if MAX_TEST_SAMPLES:
        test_df = test_df.sample(
            n=min(MAX_TEST_SAMPLES, len(test_df)), random_state=42
        ).reset_index(drop=True)
        print(f"[INFO] Subsampled test set to {len(test_df)} rows for a fast run.")

    print(f"Train: {len(train_df)} Test: {len(test_df)}")

    print(f"Loading tokenizer/model: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=2
    )

    train_dataset = EmailDataset(
        train_df["text"], train_df["label"], tokenizer, MAX_LENGTH
    )
    test_dataset = EmailDataset(
        test_df["text"], test_df["label"], tokenizer, MAX_LENGTH
    )

    training_args = TrainingArguments(
        output_dir=str(MODEL_DIR / "checkpoints"),
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE * 2,
        learning_rate=LEARNING_RATE,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_steps=50,
        report_to=[],
        save_total_limit=1,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        compute_metrics=compute_metrics,
    )

    print("\nFine tuning")
    trainer.train()

    print("\nFinal evaluation on held out test set")
    metrics = trainer.evaluate()
    for k, v in metrics.items():
        print(f" {k}: {v}")
    
    preds_output = trainer.predict(test_dataset)
    y_pred = np.argmax(preds_output.predictions, axis=1)
    print("\nConfusion matrix:\n", confusion_matrix(test_df["label"], y_pred))

    if has_source:
        print("\nPer source file breakdown on the test set:")
        eval_df = test_df.copy()
        eval_df["pred"] = y_pred
        eval_df["correct"] = eval_df["pred"] == eval_df["label"]
        per_source = eval_df.groupby("source_file").agg(
            n=("label", "size"), accuracy=("correct", "mean")
        )
        print(per_source.round(4))
        print(
            "\nCompare this table directly to the per-source-file breakdown "
            "printed by train_baseline.py — this is the core baseline-vs-BERT "
            "comparison for the thesis."
        )

    final_dir = MODEL_DIR / "final"
    trainer.save_model(str(final_dir))
    tokenizer.save_pretrained(str(final_dir))
    print(f"\nModel saved at {final_dir}")

if __name__ == "__main__":
    main()