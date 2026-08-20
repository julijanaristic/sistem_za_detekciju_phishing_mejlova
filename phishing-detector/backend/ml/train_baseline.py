from pathlib import Path 

import joblib 
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

from split_utils import get_train_test_split

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "saved_models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

def main():
    print("Loading dataset and building train/test split...")
    train_df, test_df, has_source = get_train_test_split()
    print(f"Train: {len(train_df)} Test: {len(test_df)}")
    print(f"Train class distribution:\n{train_df['label'].value_counts()}\n")

    if has_source:
        print("Source file distribution - train vs test (row counts):")
        comparison = train_df["source_file"].value_counts().to_frame("train").join(
            test_df["source_file"].value_counts().to_frame("test"), how="outer"
        ).fillna(0).astype(int)
        comparison["test_share"] = (
            comparison["test"] / (comparison["train"] + comparison["test"])
        ).round(3)
        print(comparison)
        print()
    
    X_train, y_train = train_df["text"], train_df["label"]
    X_test, y_test = test_df["text"], test_df["label"]

    print("Vectorizing text (TF-IDF)...")
    vectorizer = TfidfVectorizer(
        max_features=20000,
        ngram_range=(1, 2),
        stop_words="english",
        sublinear_tf=True,
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    print("Training Logistic Regression...")
    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(X_train_vec, y_train)

    print("\nEvaluation on held out test set (stratified by source+label)")
    y_pred = model.predict(X_test_vec)
    y_proba = model.predict_proba(X_test_vec)[:, 1]

    print(classification_report(y_test, y_pred, target_names=["legitimate", "phishing"]))
    print("Confusion matrix:\n", confusion_matrix(y_test, y_pred))
    print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.4f}")

    if has_source:
        print("\nPer-source-file breakdown on the test set:")
        eval_df = test_df.copy()
        eval_df["pred"] = y_pred
        eval_df["correct"] = eval_df["pred"] == eval_df["label"]
        per_source = eval_df.groupby("source_file").agg(
            n=("label", "size"), accuracy=("correct", "mean")
        )
        print(per_source.round(4))
    
    joblib.dump(model, MODEL_DIR / "baseline_model.joblib")
    joblib.dump(vectorizer, MODEL_DIR / "tfidf_vectorizer.joblib")
    print(f"\nModel saved at {MODEL_DIR}")

if __name__ == "__main__":
    main()