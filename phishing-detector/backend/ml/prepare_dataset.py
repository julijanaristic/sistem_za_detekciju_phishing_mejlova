from pathlib import Path 
import pandas as pd 

RAW_DIR = Path(__file__).resolve().parent / "data" / "raw"
OUTPUT_PATH = RAW_DIR / "phishing_dataset.csv"

SKIP_FILES = {"phishing_dataset.csv", "phishing_email.csv"}

LABEL_CANDIDATES = ["label", "Label", "class", "Class", "Email Type", "type"]

TEXT_CANDIDATES = ["text_combined", "text", "Text", "Email Text", "content"]

LABEL_TEXT_MAP = {
    "phishing email": 1, "phishing": 1, "spam": 1, "phish": 1,
    "safe email": 0, "legitimate": 0, "ham": 0, "0": 0, "legit": 0,
}

def normalize_label(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().any():
        return numeric 
    return series.astype(str).str.strip().str.lower().map(LABEL_TEXT_MAP)

def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    
    return None 

def load_and_normalize(path: Path) -> pd.DataFrame | None:
    try:
        df = pd.read_csv(path, encoding="utf-8", on_bad_lines="skip", low_memory=False)
    except:
        df = pd.read_csv(path, encoding="latin-1", on_bad_lines="skip", low_memory=False)
    
    label_col = find_column(df, LABEL_CANDIDATES)
    if label_col is None:
        print(f"  [SKIP] {path.name}: no label column. Columns: {list(df.columns)}")
        return None
 
    text_col = find_column(df, TEXT_CANDIDATES)
 
    if text_col is not None:
        text = df[text_col].fillna("").astype(str)
    elif {"subject", "body"}.issubset(set(c.lower() for c in df.columns)):
        subj_col = next(c for c in df.columns if c.lower() == "subject")
        body_col = next(c for c in df.columns if c.lower() == "body")
        text = df[subj_col].fillna("").astype(str) + "\n" + df[body_col].fillna("").astype(str)
    elif "body" in [c.lower() for c in df.columns]:
        body_col = next(c for c in df.columns if c.lower() == "body")
        text = df[body_col].fillna("").astype(str)
    else:
        print(f"  [SKIP] {path.name}: no text column. Columns: {list(df.columns)}")
        return None
 
    label = normalize_label(df[label_col])
 
    out = pd.DataFrame({"text": text, "label": label, "source_file": path.stem})
    out = out.dropna(subset=["text", "label"])
    out = out[out["text"].str.strip() != ""]
    out["label"] = out["label"].astype(int)
 
    print(f"  [OK] {path.name}: {len(out)} rows (text column: '{text_col or 'subject+body'}', label column: '{label_col}')")
    return out
 
 
def main():
    csv_files = sorted(p for p in RAW_DIR.glob("*.csv") if p.name not in SKIP_FILES)
 
    if not csv_files:
        raise FileNotFoundError(
            f"No CSVs in {RAW_DIR}."
        )
 
    print(f"Found {len(csv_files)} files. Processing:\n")
 
    frames = []
    for path in csv_files:
        df = load_and_normalize(path)
        if df is not None:
            frames.append(df)
 
    if not frames:
        raise RuntimeError("No file loaded.")
 
    combined = pd.concat(frames, ignore_index=True)
    before = len(combined)
    combined = combined.drop_duplicates(subset=["text"])
    after = len(combined)
 
    print(f"\nBefore dedupe: {before}")
    print(f"After dedupe: {after}")
    print(f"Class distribution:\n{combined['label'].value_counts()}")
    print(f"\nSource:\n{combined.groupby(['source_file', 'label']).size()}")
 
    combined[["text", "label"]].to_csv(OUTPUT_PATH, index=False)
    print(f"\Saved: {OUTPUT_PATH}")

    diag_path = RAW_DIR / "phishing_dataset_with_source.csv"
    combined[["text", "label", "source_file"]].to_csv(diag_path, index=False)
    print(f"Saved (diagnostics): {diag_path}")
 
 
if __name__ == "__main__":
    main()