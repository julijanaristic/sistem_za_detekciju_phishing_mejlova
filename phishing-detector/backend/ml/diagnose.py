from pathlib import Path
import itertools

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score, roc_auc_score

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
MODEL_DIR = BASE_DIR / "saved_models"

DIAG_DATA_PATH = RAW_DIR / "phishing_dataset_with_source.csv"

TOP_N_FEATURES = 30

def print_top_features():
    model_path = MODEL_DIR / "baseline_model.joblib"
    vec_path = MODEL_DIR / "tfidf_vectorizer.joblib"

    if not model_path.exists() or not vec_path.exists():
        print("[SKIP] No trained model found. Run ml/train_baseline.py first.\n")
        return

    model: LogisticRegression = joblib.load(model_path)
    vectorizer: TfidfVectorizer = joblib.load(vec_path)

    feature_names = np.array(vectorizer.get_feature_names_out())
    coefs = model.coef_[0]

    top_phishing_idx = np.argsort(coefs)[::-1][:TOP_N_FEATURES]
    top_legit_idx = np.argsort(coefs)[:TOP_N_FEATURES]

    print("=" * 70)
    print("TOP FEATURES PUSHING TOWARDS 'PHISHING' (label=1)")
    print("=" * 70)
    for i in top_phishing_idx:
        print(f"  {feature_names[i]:<30} weight={coefs[i]:+.4f}")

    print()
    print("=" * 70)
    print("TOP FEATURES PUSHING TOWARDS 'LEGITIMATE' (label=0)")
    print("=" * 70)
    for i in top_legit_idx:
        print(f"  {feature_names[i]:<30} weight={coefs[i]:+.4f}")

    print()
    print(
        "Interpretation: if the 'legitimate' list is dominated by corpus-\n"
        "specific jargon (company names, internal terminology, ids/codes)\n"
        "rather than general everyday language, and the 'phishing' list is\n"
        "dominated by a different corpus's idiosyncrasies rather than\n"
        "generic urgency/credential-harvesting language, the model is very\n"
        "likely keying off SOURCE FILE rather than phishing style.\n"
    )

def run_loco():
    if not DIAG_DATA_PATH.exists():
        print(
            f"[SKIP] {DIAG_DATA_PATH} not found.\n"
            "Add the source_file-preserving save step to prepare_dataset.py "
            "and re-run it first.\n"
        )
        return

    df = pd.read_csv(DIAG_DATA_PATH)
    df = df.dropna(subset=["text", "label", "source_file"])

    sources_by_label = (
        df.groupby(["source_file", "label"]).size().unstack(fill_value=0)
    )
    print("=" * 70)
    print("SOURCE FILE / LABEL BREAKDOWN")
    print("=" * 70)
    print(sources_by_label)
    print()

    legit_sources = sorted(df[df["label"] == 0]["source_file"].unique())
    phishing_sources = sorted(df[df["label"] == 1]["source_file"].unique())

    if len(legit_sources) < 2 or len(phishing_sources) < 2:
        print(
            "[SKIP] Need at least 2 distinct source files per class to run "
            "leave-one-corpus-out. Found:\n"
            f"  legit sources:    {legit_sources}\n"
            f"  phishing sources: {phishing_sources}\n"
        )
        return

    print("=" * 70)
    print("LEAVE-ONE-CORPUS-OUT EVALUATION")
    print("(train on all sources except one held-out legit + one held-out")
    print(" phishing source, test only on those held-out sources)")
    print("=" * 70)

    results = []

    # Cap combinations so this stays fast if there are many source files.
    combos = list(itertools.product(legit_sources, phishing_sources))
    for held_out_legit, held_out_phish in combos:
        held_out = {held_out_legit, held_out_phish}

        train_df = df[~df["source_file"].isin(held_out)]
        test_df = df[df["source_file"].isin(held_out)]

        if train_df["label"].nunique() < 2 or test_df.empty:
            continue

        vectorizer = TfidfVectorizer(
            max_features=20000,
            ngram_range=(1, 2),
            stop_words="english",
            sublinear_tf=True,
        )
        X_train = vectorizer.fit_transform(train_df["text"])
        X_test = vectorizer.transform(test_df["text"])

        model = LogisticRegression(max_iter=1000, class_weight="balanced")
        model.fit(X_train, train_df["label"])

        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        f1 = f1_score(test_df["label"], y_pred)
        try:
            auc = roc_auc_score(test_df["label"], y_proba)
        except ValueError:
            auc = float("nan")  # only one class present in this held-out pair

        results.append(
            {
                "held_out_legit": held_out_legit,
                "held_out_phishing": held_out_phish,
                "n_test": len(test_df),
                "f1": f1,
                "roc_auc": auc,
            }
        )

        print(
            f"  held out legit='{held_out_legit}' phishing='{held_out_phish}' "
            f"-> n_test={len(test_df):5d}  F1={f1:.4f}  ROC-AUC={auc:.4f}"
        )

    if results:
        res_df = pd.DataFrame(results)
        print()
        print("-" * 70)
        print(f"Mean F1 across held-out combinations:      {res_df['f1'].mean():.4f}")
        print(f"Mean ROC-AUC across held-out combinations:  {res_df['roc_auc'].mean():.4f}")
        print("-" * 70)
        print(
            "\nCompare these numbers to the ~0.99 you got from a random split\n"
            "over the pooled dataset. A large drop here is strong evidence\n"
            "that the original score was inflated by source/corpus leakage\n"
            "rather than the model actually learning phishing-specific\n"
            "language.\n"
        )


if __name__ == "__main__":
    print_top_features()
    run_loco()