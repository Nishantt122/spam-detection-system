"""
SPAMSHIELD AI — Model Training Pipeline

Trains and benchmarks:
    • Multinomial Naive Bayes
    • Logistic Regression
    • Linear SVM
    • Random Forest

Feature representation:
    • Word-level TF-IDF
    • Character-level TF-IDF
    • Combined sparse feature matrix

Outputs:
    • model_bundle.pkl
    • model.pkl
    • vectorizer.pkl
    • model_metadata.json
"""

from __future__ import annotations

import json
import os
import pickle
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from scipy.sparse import hstack

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PROJECT_DIR = os.path.dirname(
    BASE_DIR
)

DATASET_PATH = os.path.join(
    PROJECT_DIR,
    "dataset",
    "spam.csv"
)

if not os.path.exists(DATASET_PATH):
    DATASET_PATH = os.path.join(
        BASE_DIR,
        "spam.csv"
    )

MODEL_BUNDLE_PATH = os.path.join(
    BASE_DIR,
    "model_bundle.pkl"
)

LEGACY_MODEL_PATH = os.path.join(
    BASE_DIR,
    "model.pkl"
)

LEGACY_VECTORIZER_PATH = os.path.join(
    BASE_DIR,
    "vectorizer.pkl"
)

METADATA_PATH = os.path.join(
    BASE_DIR,
    "model_metadata.json"
)

RANDOM_STATE = 42
TEST_SIZE = 0.20


# ============================================================
# DATASET LOADING
# ============================================================

def find_column(columns, candidates):
    """
    Find a dataset column using common SMS-spam naming conventions.
    """
    normalized = {
        str(column).strip().lower(): column
        for column in columns
    }

    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]

    for column in columns:
        clean = str(column).strip().lower()
        for candidate in candidates:
            if candidate in clean:
                return column

    return None


def load_dataset():
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    # utf-8-sig handles files exported with a BOM.
    try:
        dataframe = pd.read_csv(
            DATASET_PATH,
            encoding="utf-8-sig"
        )
    except UnicodeDecodeError:
        dataframe = pd.read_csv(
            DATASET_PATH,
            encoding="latin-1"
        )

    if dataframe.empty:
        raise ValueError(
            "The spam dataset is empty."
        )

    label_column = find_column(
        dataframe.columns,
        [
            "label",
            "category",
            "class",
            "target",
            "v1",
        ]
    )

    message_column = find_column(
        dataframe.columns,
        [
            "message",
            "text",
            "sms",
            "content",
            "body",
            "v2",
        ]
    )

    # Fallback for a simple two-column CSV.
    if label_column is None or message_column is None:
        if len(dataframe.columns) >= 2:
            label_column = dataframe.columns[0]
            message_column = dataframe.columns[1]
        else:
            raise ValueError(
                "Dataset must contain a label column and a message/text column."
            )

    data = dataframe[
        [label_column, message_column]
    ].copy()

    data.columns = [
        "label",
        "message",
    ]

    data["message"] = (
        data["message"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    data["label"] = (
        data["label"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    data = data[
        data["message"].str.len() > 0
    ]

    def normalize_label(value):
        value = str(value).strip().lower()

        if value in {
            "spam",
            "1",
            "true",
            "yes",
        }:
            return "spam"

        if value in {
            "ham",
            "safe",
            "0",
            "false",
            "no",
            "not spam",
            "not_spam",
        }:
            return "ham"

        return None

    data["label"] = data["label"].map(
        normalize_label
    )

    data = data.dropna(
        subset=["label"]
    )

    data = data.drop_duplicates(
        subset=["message"],
        keep="first"
    )

    if data["label"].nunique() < 2:
        raise ValueError(
            "The dataset must contain both spam and ham examples."
        )

    return data.reset_index(
        drop=True
    )


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(y_true, y_pred):
    return {
        "accuracy": round(
            float(
                accuracy_score(
                    y_true,
                    y_pred
                ) * 100
            ),
            2
        ),
        "precision": round(
            float(
                precision_score(
                    y_true,
                    y_pred,
                    pos_label="spam",
                    zero_division=0
                ) * 100
            ),
            2
        ),
        "recall": round(
            float(
                recall_score(
                    y_true,
                    y_pred,
                    pos_label="spam",
                    zero_division=0
                ) * 100
            ),
            2
        ),
        "f1": round(
            float(
                f1_score(
                    y_true,
                    y_pred,
                    pos_label="spam",
                    zero_division=0
                ) * 100
            ),
            2
        ),
    }


# ============================================================
# TRAINING
# ============================================================

def main():
    print("=" * 70)
    print("SPAMSHIELD AI — MODEL TRAINING")
    print("=" * 70)

    data = load_dataset()

    X = data["message"]
    y = data["label"]

    print(f"Dataset: {DATASET_PATH}")
    print(f"Total samples: {len(data):,}")
    print(
        f"Spam: {(y == 'spam').sum():,} | "
        f"Ham: {(y == 'ham').sum():,}"
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y
    )

    print(
        f"Training samples: {len(X_train):,}"
    )
    print(
        f"Test samples: {len(X_test):,}"
    )

    # --------------------------------------------------------
    # WORD TF-IDF
    # --------------------------------------------------------

    print("\nBuilding word-level TF-IDF...")

    word_vectorizer = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 2),
        min_df=1,
        max_df=0.98,
        sublinear_tf=True,
        max_features=100000
    )

    X_train_word = word_vectorizer.fit_transform(
        X_train
    )

    X_test_word = word_vectorizer.transform(
        X_test
    )

    # --------------------------------------------------------
    # CHARACTER TF-IDF
    # --------------------------------------------------------

    print("Building character-level TF-IDF...")

    char_vectorizer = TfidfVectorizer(
        analyzer="char",
        lowercase=True,
        ngram_range=(3, 5),
        min_df=1,
        max_df=0.99,
        sublinear_tf=True,
        max_features=100000
    )

    X_train_char = char_vectorizer.fit_transform(
        X_train
    )

    X_test_char = char_vectorizer.transform(
        X_test
    )

    # --------------------------------------------------------
    # COMBINED FEATURES
    # --------------------------------------------------------

    X_train_features = hstack(
        [
            X_train_word,
            X_train_char,
        ]
    ).tocsr()

    X_test_features = hstack(
        [
            X_test_word,
            X_test_char,
        ]
    ).tocsr()

    print(
        "Combined feature matrix:",
        X_train_features.shape
    )

    # --------------------------------------------------------
    # MODELS
    # --------------------------------------------------------

    models = {
        "Multinomial Naive Bayes": MultinomialNB(
            alpha=0.1
        ),

        "Logistic Regression": LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=RANDOM_STATE
        ),

        "Linear SVM": LinearSVC(
            C=1.5,
            class_weight="balanced",
            random_state=RANDOM_STATE
        ),

        "Random Forest": RandomForestClassifier(
            n_estimators=250,
            max_depth=None,
            min_samples_leaf=1,
            class_weight="balanced",
            n_jobs=-1,
            random_state=RANDOM_STATE
        ),
    }

    benchmark = {}
    trained_models = {}

    print("\n" + "=" * 70)
    print("MODEL BENCHMARK")
    print("=" * 70)

    for name, model in models.items():
        print(f"\nTraining {name}...")

        model.fit(
            X_train_features,
            y_train
        )

        predictions = model.predict(
            X_test_features
        )

        metrics = calculate_metrics(
            y_test,
            predictions
        )

        benchmark[name] = metrics
        trained_models[name] = model

        print(
            f"Accuracy : {metrics['accuracy']:.2f}%"
        )
        print(
            f"Precision: {metrics['precision']:.2f}%"
        )
        print(
            f"Recall   : {metrics['recall']:.2f}%"
        )
        print(
            f"F1       : {metrics['f1']:.2f}%"
        )

    # --------------------------------------------------------
    # BEST MODEL
    # --------------------------------------------------------

    best_model_name = max(
        benchmark,
        key=lambda name: (
            benchmark[name]["f1"],
            benchmark[name]["accuracy"],
            benchmark[name]["precision"],
            benchmark[name]["recall"]
        )
    )

    print("\n" + "=" * 70)
    print(
        f"BEST MODEL: {best_model_name}"
    )
    print("=" * 70)

    print(
        json.dumps(
            benchmark[best_model_name],
            indent=4
        )
    )

    # --------------------------------------------------------
    # ENSEMBLE WEIGHTS
    # --------------------------------------------------------
    #
    # F1-based normalized weights make stronger models
    # contribute more without hard-coding benchmark numbers.
    # --------------------------------------------------------

    raw_weights = {
        name: max(
            benchmark[name]["f1"],
            0.01
        )
        for name in trained_models
    }

    weight_total = sum(
        raw_weights.values()
    )

    ensemble_weights = {
        name: round(
            weight / weight_total,
            6
        )
        for name, weight in raw_weights.items()
    }

    # Correct floating-point rounding drift so the stored
    # weights sum to exactly 1.0.
    if ensemble_weights:
        difference = round(
            1.0 - sum(
                ensemble_weights.values()
            ),
            6
        )

        ensemble_weights[
            best_model_name
        ] = round(
            ensemble_weights[best_model_name]
            + difference,
            6
        )

    print("\nEnsemble weights:")
    for name, weight in ensemble_weights.items():
        print(
            f"  {name}: {weight:.6f}"
        )

    # --------------------------------------------------------
    # FULL-DATA LEGACY MODEL
    # --------------------------------------------------------
    #
    # Keep the old model/vectorizer files for compatibility
    # with deployments that still use the legacy engine.
    # --------------------------------------------------------

    print("\nTraining legacy compatibility model...")

    legacy_vectorizer = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 2),
        sublinear_tf=True,
        max_features=100000
    )

    X_full_legacy = (
        legacy_vectorizer.fit_transform(
            X
        )
    )

    legacy_model = LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        random_state=RANDOM_STATE
    )

    legacy_model.fit(
        X_full_legacy,
        y
    )

    # --------------------------------------------------------
    # SAVE ENSEMBLE BUNDLE
    # --------------------------------------------------------

    bundle = {
        "platform": "SPAMSHIELD AI",

        "version": "SPAMSHIELD-AI-1.0",

        "word_vectorizer": word_vectorizer,

        "char_vectorizer": char_vectorizer,

        "models": trained_models,

        "ensemble_weights": ensemble_weights,

        "best_model": best_model_name,

        "feature_config": {
            "word_ngram_range": [1, 2],
            "char_ngram_range": [3, 5],
            "word_max_features": 100000,
            "char_max_features": 100000,
            "test_size": TEST_SIZE,
            "random_state": RANDOM_STATE
        }
    }

    with open(
        MODEL_BUNDLE_PATH,
        "wb"
    ) as file:
        pickle.dump(
            bundle,
            file,
            protocol=pickle.HIGHEST_PROTOCOL
        )

    # --------------------------------------------------------
    # SAVE LEGACY FILES
    # --------------------------------------------------------

    with open(
        LEGACY_MODEL_PATH,
        "wb"
    ) as file:
        pickle.dump(
            legacy_model,
            file,
            protocol=pickle.HIGHEST_PROTOCOL
        )

    with open(
        LEGACY_VECTORIZER_PATH,
        "wb"
    ) as file:
        pickle.dump(
            legacy_vectorizer,
            file,
            protocol=pickle.HIGHEST_PROTOCOL
        )

    # --------------------------------------------------------
    # METADATA FOR MODEL CENTER
    # --------------------------------------------------------

    metadata = {
        "platform": "SPAMSHIELD AI",
        "version": "SPAMSHIELD-AI-1.0",
        "model_version": "SPAMSHIELD-AI-1.0",
        "engine": "ensemble",
        "best_model": best_model_name,

        "dataset": {
            "path": os.path.relpath(
                DATASET_PATH,
                PROJECT_DIR
            ),
            "samples": int(len(data)),
            "spam_samples": int(
                (y == "spam").sum()
            ),
            "ham_samples": int(
                (y == "ham").sum()
            ),
            "test_size": TEST_SIZE,
            "random_state": RANDOM_STATE
        },

        "features": {
            "word_tfidf": {
                "ngram_range": [1, 2],
                "max_features": 100000,
                "sublinear_tf": True
            },
            "char_tfidf": {
                "ngram_range": [3, 5],
                "max_features": 100000,
                "sublinear_tf": True
            }
        },

        "models": [
            {
                "name": name,
                **benchmark[name],
                "ensemble_weight": ensemble_weights[name],
                "best": (
                    name == best_model_name
                )
            }
            for name in benchmark
        ],

        # Also keep the dict form for compatibility with
        # earlier frontend/backend metadata readers.
        "model_metrics": benchmark,

        "ensemble_weights": ensemble_weights,

        "trained_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "training_status": "success"
    }

    with open(
        METADATA_PATH,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            metadata,
            file,
            indent=4
        )

    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TRAINING COMPLETE")
    print("=" * 70)

    print(
        f"Best model : {best_model_name}"
    )
    print(
        f"Accuracy   : "
        f"{benchmark[best_model_name]['accuracy']:.2f}%"
    )
    print(
        f"Precision  : "
        f"{benchmark[best_model_name]['precision']:.2f}%"
    )
    print(
        f"Recall     : "
        f"{benchmark[best_model_name]['recall']:.2f}%"
    )
    print(
        f"F1 Score   : "
        f"{benchmark[best_model_name]['f1']:.2f}%"
    )

    print("\nFiles created:")
    print(
        f"  ✓ {MODEL_BUNDLE_PATH}"
    )
    print(
        f"  ✓ {LEGACY_MODEL_PATH}"
    )
    print(
        f"  ✓ {LEGACY_VECTORIZER_PATH}"
    )
    print(
        f"  ✓ {METADATA_PATH}"
    )


if __name__ == "__main__":
    main()
