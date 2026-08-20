from pathlib import Path
 
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.pipeline import Pipeline
 
DATA_PATH = Path(__file__).resolve().parent / "data" / "raw" / "phishing_dataset.csv"
 
def main():
    df = pd.read_csv(DATA_PATH).dropna(subset=["text", "label"])
    print(f"{len(df)} examples loaded.\n")
 
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=20000, ngram_range=(1, 2), stop_words="english")),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
 
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(pipeline, df["text"], df["label"], cv=cv, scoring="f1", n_jobs=-1)
 
    print("F1 per fold:", [round(s, 4) for s in scores])
    print(f"Mean: {scores.mean():.4f}  Std: {scores.std():.4f}")
    print(
        "\nIF std is < 0.01 iand all of the folds are similar -> result is stable,"
    )
 
 
if __name__ == "__main__":
    main()