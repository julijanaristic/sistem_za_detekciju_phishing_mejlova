from pathlib import Path 

import pandas as pd 
from sklearn.model_selection import train_test_split 

BASE_DIR = Path(__file__).resolve().parent 
RAW_DIR = BASE_DIR / "data" / "raw"

DATA_PATH_WITH_SOURCE = RAW_DIR / "phishing_dataset_with_source.csv"
DATA_PATH_PLAIN = RAW_DIR / "phishing_dataset.csv"

MIN_GROUP_SIZE_FOR_STRATIFY = 2
RANDOM_STATE = 42
TEST_SIZE = 0.2

def load_dataset() -> tuple[pd.DataFrame, bool]:
    """Returns (dataframe, has_source_file)"""
    if DATA_PATH_WITH_SOURCE.exists():
        df = pd.read_csv(DATA_PATH_WITH_SOURCE)
        has_source = "source_file" in df.columns
    elif DATA_PATH_PLAIN.exists():
        print(
            f"[WARN] {DATA_PATH_WITH_SOURCE.name} not found, falling back to "
            f"{DATA_PATH_PLAIN.name}. Split will NOT be stratified by source "
            "file.\n"
        )
        df = pd.read_csv(DATA_PATH_PLAIN)
        has_source = False 
    else:
        raise FileNotFoundError(
            f"No dataset found. Expected {DATA_PATH_WITH_SOURCE} or "
            f"{DATA_PATH_PLAIN}. Run ml/prepare_dataset.py first."
        )

    if "text" not in df.columns and {"subject", "body"}.issubset(df.columns):
        df["text"] = df["subject"].fillna("") + "\n" + df["body"].fillna("")
    
    df = df.dropna(subset=["text", "label"])
    df["label"] = df["label"].astype(int)
    return df, has_source 

def make_stratify_key(df: pd.DataFrame) -> pd.Series:
    key = df["source_file"].astype(str) + "__" + df["label"].astype(str)
    counts = key.value_counts()
    rare = counts[counts < MIN_GROUP_SIZE_FOR_STRATIFY].index 
    if len(rare) > 0:
        print(
            f"[INFO] {len(rare)} source/label combinations have fewer than "
            f"{MIN_GROUP_SIZE_FOR_STRATIFY} rows and will be grouped into a "
            "single 'rare' stratify bucket."
        )
    return key.where(~key.isin(rare), other="rare")

def get_train_test_split() -> tuple[pd.DataFrame, pd.DataFrame, bool]:
    df, has_source = load_dataset()

    if has_source:
        stratify_key = make_stratify_key(df)
        train_idx, test_idx = train_test_split(
            df.index,
            test_size=TEST_SIZE,
            random_state=RANDOM_STATE,
            stratify=stratify_key,
        )
        train_df = df.loc[train_idx].reset_index(drop=True)
        test_df = df.loc[test_idx].reset_index(drop=True)

    else:
        train_df, test_df = train_test_split(
            df, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=df["label"]
        )
        train_df = train_df.reset_index(drop=True)
        test_df = test_df.reset_index(drop=True)
    
    return train_df, test_df, has_source