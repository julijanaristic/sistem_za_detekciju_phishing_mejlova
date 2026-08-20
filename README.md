# Phishing Email Detection System

A web-based system for detecting phishing emails using Natural Language
Processing (NLP) and machine learning.

The system supports two classification approaches:

- TF-IDF + Logistic Regression baseline
- Fine-tuned DistilBERT classifier

It also provides additional heuristic analysis of email senders and URLs
and supports integration with Gmail through OAuth 2.0.

---

## System Architecture

The system consists of:

- React + TypeScript frontend
- FastAPI backend
- TF-IDF + Logistic Regression classifier
- Fine-tuned DistilBERT classifier
- Sender and URL analysis module
- Gmail API integration
- Factory pattern for classifier selection

The active classifier can be selected through the backend configuration.

---

## Requirements

Before running the application, make sure the following software is installed:

- Python 3.10+
- Node.js 18+
- npm
- Git

For BERT inference and training:

- PyTorch
- Transformers

A GPU is recommended for BERT training, although the training script can
also be executed on a CPU.

---

# Running the Application

The project consists of two separate parts:

- `backend` - FastAPI REST API and machine learning models
- `frontend` - React + TypeScript user interface

Both parts need to be started separately.

---

## 1. Backend

Open a terminal and navigate to the backend directory:

```bash
cd backend
```

Create and activate a Python virtual environment:

```
python -m venv .venv
source .venv/Scripts/activate
```

Install the required Python packages:

```
pip install -r requirements.txt
```

Start the FastAPI server:

```
uvicorn app.main:main --reload
```

The backend will be available at:

```
http://localhost:8000
```
## 2. Frontend

Open a second terminal and navigate to the frontend directory:

```
cd frontend
```

Install the required Node.js packages:

```
npm install
```

Start the development server:

```
npm run dev
```

The frontend will then be available at the address displayed by Vite, typically:

```
http://localhost:5173
```

# Selecting the Classification Model

The backend supports two classification models:
1. TF-IDF + Logistic Regression
2. Fine-tuned DistilBERT

The active model is selected in the backend configuration.

For the baseline model: ACTIVE_MODEL=baseline

For the DistilBERT model: ACTIVE_MODEL=bert

The corresponding trained model files must be available in the expected ml/saved_models/ directory

# Training the Models

The trained machine learning models are not included in the repository.

This is intentional because the trained model files and datasets can be large, while training the models can require significant computational resources.

The repository contains the scripts necessary to prepare the dataset, train the baseline model and fine-tune the DistilBERT model.

## 1. Preparing the Dataset

### Dataset source

The datasets used in this project are publicly available phishing/legitimate
email corpora. Download the following CSV files and place them in
`backend/ml/data/raw/`:

- CEAS_08.csv
- Enron.csv
- Ling.csv
- Nazario.csv
- Nigerian_Fraud.csv
- SpamAssassin.csv

Each file is expected to contain either a text column, or separate
subject and body columns (in which case prepare_dataset.py will
combine them into text), plus a label column (1 = phishing,
0 = legitimate).

### Running dataset preparation

Place the required CSV datasets in backend/ml/data/raw, then run:
```
cd backend
python ml/prepare_dataset.py
```
The script:
- loads the available CSV datasets,
- identifies the text and label columns,
- normalizes the labels,
- combines the datasets,
- removes duplicate emails,
- preserves information about the source dataset for diagnostics.

This produces phishing_dataset_with_source.csv (and a plain
phishing_dataset.csv fallback without the source_file column), which
are used by all training and evaluation scripts.

## 2. Training the TF-IDF + Logistic Regression Baseline

The baseline model uses:
- TF-IDF text representation
- unigram and bigram features
- English stop-word removal
- Logistic Regression classifier

To train it, run:

```
cd backend
python ml/train_baseline.py
```
The trained model and TF-IDF vectorizer are saved to: backend/ml/saved_models/

The baseline model is relatively fast to train and can normally be trained
on a CPU.

## 3. Training the DistilBERT Model

The second classification approach uses a fine-tuned: distilbert-base-uncased

The training configuration is defined in: backend/ml/train_bert.py

The script uses the same train/test split as the baseline model so that the
two approaches can be compared on identical data.

To start BERT training:
```
cd backend
python ml/train_bert.py
```
The script performs the following steps:
- Loads the prepared dataset.
- Creates the train/test split.
- Loads the DistilBERT tokenizer and model.
- Tokenizes the email text.
- Fine-tunes DistilBERT for binary classification.
- Evaluates the model using accuracy, precision, recall, F1-score and ROC-AUC.
- Saves the final model and tokenizer.

The resulting model is saved in: backend/ml/saved_models/bert/final/

## BERT Training on CPU

The BERT training script can be executed on a CPU:

```
cd backend
python ml/train_bert.py
```

However, training on a CPU can take a significant amount of time,
especially when the complete dataset is used.

For testing the training pipeline before running the full experiment,
the following parameters in ml/train_bert.py can be reduced:

```
MAX_TRAIN_SAMPLES = 5000
MAX_TEST_SAMPLES = 1500
```

This allows the complete training pipeline to be tested on a smaller
subset of the dataset.

For the final experiment, these values should be set to:

```
MAX_TRAIN_SAMPLES = None
MAX_TEST_SAMPLES = None
```

This enables training on the complete train and test splits.

## Training BERT using Google Colab

If local CPU training is too slow (fine-tuning DistilBERT on the full
~66k-row train set can take hours per epoch on CPU), the recommended
approach is to run ml/train_bert.py on a free Colab GPU runtime instead.
On a T4 GPU, the full 2-epoch run takes roughly 1.5–2 hours; on CPU, budget
several hours per epoch.

### Steps

1. **Open Colab and enable a GPU runtime.**
   Go to [colab.research.google.com](https://colab.research.google.com) →
   New notebook → Runtime → Change runtime type → set Hardware
   accelerator to **GPU** (T4 is sufficient and free).

2. **Package and upload the project.**
   Zip the backend/ml/ folder (scripts + data/raw/ with all six CSV
   files) locally, then upload the zip via the Colab file panel, or upload
   it to Google Drive and mount the Drive instead (more reliable for larger
   files).

3. **Unzip, always from a known working directory.**
   ```
   %cd /content
   !rm -rf /content/ml
   !unzip -q ml.zip -d /content/
   ```
   Always %cd /content before any rm -rf — if your shell's current
   directory has been changed by an earlier %cd ml and you then delete
   that same directory, getcwd() breaks and every subsequent ! command
   fails with a cannot access parent directories error.

4. **Verify the upload.**
   ```
   !ls /content/ml/data/raw
   ```
   Confirm all 6 source files are present.

5. **Install dependencies.**
   ```
   !pip install -q transformers torch scikit-learn accelerate
   ```
   Colab's PyTorch already ships with CUDA support, so no extra GPU setup
   is needed.

6. **Confirm the GPU is actually visible** (optional but recommended,
   catches a misconfigured runtime before wasting time on a full run):
   ```
   import torch
   print(torch.cuda.is_available(), torch.cuda.get_device_name(0))
   ```

7. **Check train_bert.py settings.**
   Make sure MAX_TRAIN_SAMPLES and MAX_TEST_SAMPLES are set to None
   (not the smoke-test values 5000/1500) before running the full,
   thesis-grade training run.

8. **Run training.**
   ```
   %cd /content/ml
   !python train_bert.py
   ```

9. **Retrieve the trained model.**
   Colab sessions are ephemeral — local files (including
   saved_models/bert/final/) are deleted when the runtime disconnects or
   resets. As soon as training finishes:

   - **Do not zip the whole saved_models/bert/ folder.** It also
     contains checkpoints/, which includes the optimizer state
     (optimizer.pt) — typically 2x the size of the model itself and not
     needed for inference or for the thesis. Zip only the final/
     directory:
     ```
     %cd /content
     !zip -r results.zip ml/saved_models/bert/final
     ```
   - Download results.zip via the Colab file panel, **or**, more
     reliably for larger files, copy it to Google Drive:
     ```
     from google.colab import drive
     drive.mount('/content/drive')
     !cp results.zip /content/drive/MyDrive/
     ```

10. **Copy the result back into the project.**
    Unzip results.zip locally so that the trained model ends up at
    backend/ml/saved_models/bert/final/.

The BERT training script does not require any code changes to use a GPU —
PyTorch automatically selects CUDA when available, via:

```
torch.device("cuda" if torch.cuda.is_available() else "cpu")
```
# Gmail Integration

The application can connect to a Gmail account using the Gmail API and OAuth 2.0.

To use this functionality, Google OAuth credentials must be configured through environment variables.

Create a .env file in the backend directory containing the required Google credentials.

An example configuration can be provided in: .env.example

Do not commit the actual .env file or OAuth credentials to the repository.

After starting the backend and frontend, the Gmail connection can be initiated through the application's interface.

# Project structure

```
project/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   └── services/
│   │       ├── classifier/
│   │       └── gmail/
│   │
│   ├── ml/
│   │   ├── data/
│   │   ├── saved_models/
│   │   ├── diagnose.py
│   │   ├── prepare_dataset.py
│   │   ├── sanity_check.py
│   │   ├── split_utils.py
│   │   ├── train_baseline.py
│   │   └── train_bert.py
│   │
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
│
└── README.md
```

# Additional Email Analysis

In addition to the machine learning classification, the backend performs additional heuristic analysis.

## Sender analysis

The sender domain can be compared against a list of known legitimate domains.

## URL analysis

URLs contained in an email can be examined for several suspicious characteristics, including:

- use of an IP address instead of a domain,
- lack of HTTPS,
- domains that resemble known brands,
- excessive subdomain depth.

These findings are returned together with the classification result and
can be displayed in the frontend.

# Evaluation

The project contains several scripts for evaluating the classification models.

The baseline evaluation is performed using the same train/test split that is used for BERT, allowing a direct comparison between the two approaches.

Additional diagnostic evaluation is available through: python ml/diagnose.py

This includes:

- analysis of the most influential TF-IDF features,
- Leave-One-Corpus-Out (LOCO) evaluation.

The LOCO evaluation is used as a stricter test of model generalization and helps identify possible source/corpus leakage in the dataset.

# Important Notes

The repository does not contain:

- the Python virtual environment,
- .env files,
- Gmail OAuth tokens,
- raw datasets,
- trained machine learning models.

These files are intentionally excluded from version control.

The required dependencies are specified in: backend/requirements.txt

and the machine learning models can be generated using the provided
training scripts.
