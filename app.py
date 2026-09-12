from flask import Flask, request, jsonify
from flask_cors import CORS

import json
import os
import pickle
import re

import numpy as np
from scipy.special import expit
from scipy.sparse import hstack


# ============================================================
# SPAMSHIELD AI — PRODUCTION API
# ============================================================

app = Flask(__name__)
CORS(app)


# ============================================================
# FILE PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
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


# ============================================================
# GLOBAL AI ENGINE
# ============================================================

bundle = None
legacy_model = None
legacy_vectorizer = None
metadata = {}

ENGINE_MODE = "unavailable"


# ============================================================
# LOAD MODELS
# ============================================================

def load_models():

    global bundle
    global legacy_model
    global legacy_vectorizer
    global metadata
    global ENGINE_MODE

    # --------------------------------------------------------
    # Load new SPAMSHIELD AI ensemble
    # --------------------------------------------------------

    if os.path.exists(MODEL_BUNDLE_PATH):

        try:

            with open(
                MODEL_BUNDLE_PATH,
                "rb"
            ) as file:

                bundle = pickle.load(file)

            ENGINE_MODE = "ensemble"

            print(
                "SPAMSHIELD AI ensemble loaded successfully."
            )

        except Exception as error:

            print(
                "Could not load ensemble:",
                error
            )

            bundle = None


    # --------------------------------------------------------
    # Legacy fallback
    # --------------------------------------------------------

    if bundle is None:

        if os.path.exists(
            LEGACY_MODEL_PATH
        ):

            try:

                with open(
                    LEGACY_MODEL_PATH,
                    "rb"
                ) as file:

                    legacy_model = pickle.load(
                        file
                    )

            except Exception as error:

                print(
                    "Could not load legacy model:",
                    error
                )


        if os.path.exists(
            LEGACY_VECTORIZER_PATH
        ):

            try:

                with open(
                    LEGACY_VECTORIZER_PATH,
                    "rb"
                ) as file:

                    legacy_vectorizer = pickle.load(
                        file
                    )

            except Exception as error:

                print(
                    "Could not load legacy vectorizer:",
                    error
                )


        if (
            legacy_model is not None
            and legacy_vectorizer is not None
        ):

            ENGINE_MODE = "legacy"

            print(
                "Legacy ML engine loaded."
            )


    # --------------------------------------------------------
    # Load metadata
    # --------------------------------------------------------

    if os.path.exists(
        METADATA_PATH
    ):

        try:

            with open(
                METADATA_PATH,
                "r",
                encoding="utf-8"
            ) as file:

                metadata = json.load(
                    file
                )

        except Exception as error:

            print(
                "Could not load metadata:",
                error
            )

            metadata = {}


load_models()


# ============================================================
# URL DETECTION
# ============================================================

URL_PATTERN = re.compile(
    r"(https?://[^\s]+|"
    r"www\.[^\s]+|"
    r"\b[a-zA-Z0-9.-]+\."
    r"(?:com|net|org|in|co|info|biz|xyz|top|site|"
    r"online|click|shop|live|icu|ru|tk|ml|ga|cf|gq)"
    r"(?:/[^\s]*)?)",
    re.IGNORECASE
)


SHORTENER_DOMAINS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "ow.ly",
    "is.gd",
    "buff.ly",
    "cutt.ly",
    "shorturl.at"
}


HIGH_RISK_TLDS = {
    ".xyz",
    ".top",
    ".click",
    ".live",
    ".icu",
    ".tk",
    ".ml",
    ".ga",
    ".cf",
    ".gq"
}


# ============================================================
# THREAT INTELLIGENCE KEYWORDS
# ============================================================

URGENCY_TERMS = {
    "urgent",
    "immediately",
    "immediate",
    "act now",
    "last chance",
    "expires today",
    "within 24 hours",
    "account will be blocked",
    "account suspended",
    "verify now",
    "action required"
}


FINANCIAL_TERMS = {
    "payment",
    "pay",
    "money",
    "cash",
    "refund",
    "transfer",
    "bank",
    "credit card",
    "debit card",
    "upi",
    "wallet",
    "fee",
    "prize",
    "reward",
    "lottery",
    "cashback",
    "investment"
}


CREDENTIAL_TERMS = {
    "password",
    "passcode",
    "otp",
    "pin",
    "cvv",
    "verification code",
    "login",
    "sign in",
    "verify your account",
    "confirm your identity",
    "security code"
}


IMPERSONATION_TERMS = {
    "bank",
    "paypal",
    "amazon",
    "google",
    "microsoft",
    "apple",
    "netflix",
    "instagram",
    "facebook",
    "whatsapp",
    "government",
    "income tax",
    "support team",
    "security team"
}


PROMOTIONAL_TERMS = {
    "offer",
    "discount",
    "sale",
    "deal",
    "free",
    "winner",
    "congratulations",
    "bonus",
    "coupon",
    "claim",
    "win",
    "exclusive"
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def count_matches(text, terms):

    lower_text = text.lower()

    return [
        term
        for term in terms
        if term in lower_text
    ]


def extract_urls(text):

    matches = URL_PATTERN.findall(
        text
    )

    cleaned = []

    for url in matches:

        url = url.rstrip(
            ".,!?;:)]}"
        )

        if url not in cleaned:

            cleaned.append(
                url
            )

    return cleaned


# ============================================================
# URL INTELLIGENCE
# ============================================================

def analyze_urls(text):

    urls = extract_urls(
        text
    )

    signals = []

    shorteners = []
    risky_tlds = []
    ip_urls = []
    suspicious_structure = []


    for url in urls:

        lower_url = url.lower()

        hostname = lower_url

        hostname = re.sub(
            r"^https?://",
            "",
            hostname
        )

        hostname = hostname.split(
            "/"
        )[0]

        hostname = hostname.split(
            "?"
        )[0]

        hostname = hostname.split(
            "#"
        )[0]

        if hostname.startswith(
            "www."
        ):

            hostname = hostname[4:]


        # URL shortener

        if hostname in SHORTENER_DOMAINS:

            shorteners.append(
                hostname
            )


        # Risky TLD

        if any(
            hostname.endswith(
                tld
            )
            for tld in HIGH_RISK_TLDS
        ):

            risky_tlds.append(
                hostname
            )


        # IP address URL

        ip_match = re.match(
            r"^\d{1,3}(?:\.\d{1,3}){3}$",
            hostname
        )

        if ip_match:

            ip_urls.append(
                hostname
            )


        # Suspicious URL structure

        if (
            hostname.count(".") >= 3
            or "@" in url
            or "%" in url
            or len(url) > 120
        ):

            suspicious_structure.append(
                url
            )


    if shorteners:

        signals.append(
            "URL shortener detected"
        )


    if risky_tlds:

        signals.append(
            "High-risk URL extension detected"
        )


    if ip_urls:

        signals.append(
            "IP-address URL detected"
        )


    if suspicious_structure:

        signals.append(
            "Unusual URL structure detected"
        )


    return {

        "urls": urls,

        "count": len(urls),

        "shorteners": shorteners,

        "risky_tlds": risky_tlds,

        "ip_urls": ip_urls,

        "suspicious_structure":
            suspicious_structure,

        "signals": signals
    }


# ============================================================
# SOCIAL ENGINEERING ANALYSIS
# ============================================================

def analyze_social_engineering(text):

    urgency = count_matches(
        text,
        URGENCY_TERMS
    )

    financial = count_matches(
        text,
        FINANCIAL_TERMS
    )

    credentials = count_matches(
        text,
        CREDENTIAL_TERMS
    )

    impersonation = count_matches(
        text,
        IMPERSONATION_TERMS
    )

    promotional = count_matches(
        text,
        PROMOTIONAL_TERMS
    )


    signals = []


    if urgency:

        signals.append(
            "Urgency / pressure language"
        )


    if financial:

        signals.append(
            "Financial request or incentive"
        )


    if credentials:

        signals.append(
            "Credential / OTP request"
        )


    if impersonation:

        signals.append(
            "Possible brand or organization impersonation"
        )


    if promotional:

        signals.append(
            "Promotional / reward language"
        )


    return {

        "urgency": urgency,

        "financial": financial,

        "credentials": credentials,

        "impersonation": impersonation,

        "promotional": promotional,

        "signals": signals
    }


# ============================================================
# MESSAGE FEATURE ANALYSIS
# ============================================================

def analyze_message_features(text):

    words = re.findall(
        r"\b\w+\b",
        text
    )

    digits = re.findall(
        r"\d",
        text
    )

    uppercase_letters = re.findall(
        r"[A-Z]",
        text
    )

    letters = re.findall(
        r"[A-Za-z]",
        text
    )

    special_characters = re.findall(
        r"[^A-Za-z0-9\s]",
        text
    )

    exclamations = text.count(
        "!"
    )


    uppercase_ratio = 0


    if letters:

        uppercase_ratio = (
            len(uppercase_letters)
            / len(letters)
        ) * 100


    return {

        "characters": len(text),

        "words": len(words),

        "digits": len(digits),

        "exclamations":
            exclamations,

        "special_characters":
            len(special_characters),

        "uppercase_ratio":
            round(
                uppercase_ratio,
                2
            )
    }


# ============================================================
# CONVERT MODEL OUTPUT TO SPAM PROBABILITY
# ============================================================

def sigmoid_score(value):

    try:

        return float(
            expit(value)
        )

    except Exception:

        return 0.5


def model_spam_probability(
    model,
    features
):

    # --------------------------------------------------------
    # Models supporting predict_proba
    # --------------------------------------------------------

    if hasattr(
        model,
        "predict_proba"
    ):

        probabilities = (
            model.predict_proba(
                features
            )[0]
        )

        classes = [
            str(c).lower()
            for c in model.classes_
        ]


        if "spam" in classes:

            index = classes.index(
                "spam"
            )

            return float(
                probabilities[index]
            )


        if "1" in classes:

            index = classes.index(
                "1"
            )

            return float(
                probabilities[index]
            )


        return float(
            max(probabilities)
        )


    # --------------------------------------------------------
    # Linear SVM
    # --------------------------------------------------------

    if hasattr(
        model,
        "decision_function"
    ):

        decision = model.decision_function(
            features
        )

        if isinstance(
            decision,
            np.ndarray
        ):

            decision = float(
                decision[0]
            )

        return sigmoid_score(
            decision
        )


    # --------------------------------------------------------
    # Generic prediction fallback
    # --------------------------------------------------------

    prediction = str(
        model.predict(
            features
        )[0]
    ).lower()


    return (
        1.0
        if prediction == "spam"
        else 0.0
    )


# ============================================================
# RUN ENSEMBLE
# ============================================================

def run_ensemble(message):

    if bundle is None:

        return None


    word_vectorizer = bundle[
        "word_vectorizer"
    ]

    char_vectorizer = bundle[
        "char_vectorizer"
    ]

    models = bundle[
        "models"
    ]

    weights = bundle[
        "ensemble_weights"
    ]


    # --------------------------------------------------------
    # Transform message
    # --------------------------------------------------------

    word_features = (
        word_vectorizer.transform(
            [message]
        )
    )

    char_features = (
        char_vectorizer.transform(
            [message]
        )
    )


    features = hstack(
        [
            word_features,
            char_features
        ]
    ).tocsr()


    # --------------------------------------------------------
    # Run every model
    # --------------------------------------------------------

    model_scores = {}

    weighted_score = 0

    total_weight = 0


    for name, model in models.items():

        score = model_spam_probability(
            model,
            features
        )

        weight = float(
            weights.get(
                name,
                0
            )
        )


        model_scores[name] = round(
            score * 100,
            2
        )


        weighted_score += (
            score * weight
        )

        total_weight += weight


    if total_weight > 0:

        weighted_score /= (
            total_weight
        )


    confidence = (
        max(
            weighted_score,
            1 - weighted_score
        ) * 100
    )


    return {

        "spam_probability":
            float(weighted_score),

        "confidence":
            round(
                float(confidence),
                2
            ),

        "model_scores":
            model_scores
    }


# ============================================================
# LEGACY MODEL
# ============================================================

def run_legacy(message):

    transformed = (
        legacy_vectorizer.transform(
            [message]
        )
    )


    prediction = (
        legacy_model.predict(
            transformed
        )[0]
    )


    prediction_string = str(
        prediction
    ).lower()


    if hasattr(
        legacy_model,
        "predict_proba"
    ):

        probabilities = (
            legacy_model.predict_proba(
                transformed
            )[0]
        )

        confidence = (
            max(probabilities)
            * 100
        )

        classes = [
            str(c).lower()
            for c in legacy_model.classes_
        ]


        if "spam" in classes:

            spam_probability = (
                probabilities[
                    classes.index(
                        "spam"
                    )
                ]
            )

        else:

            spam_probability = (
                1.0
                if prediction_string == "spam"
                else 0.0
            )


    else:

        spam_probability = (
            1.0
            if prediction_string == "spam"
            else 0.0
        )

        confidence = 100.0


    return {

        "spam_probability":
            float(spam_probability),

        "confidence":
            round(
                float(confidence),
                2
            ),

        "model_scores": {

            "Legacy Naive Bayes":
                round(
                    float(
                        spam_probability
                        * 100
                    ),
                    2
                )
        }
    }


# ============================================================
# THREAT CLASSIFICATION
# ============================================================

def classify_threat(
    spam_probability,
    url_info,
    social_info
):

    has_urls = (
        url_info["count"] > 0
    )

    has_credentials = bool(
        social_info["credentials"]
    )

    has_financial = bool(
        social_info["financial"]
    )

    has_urgency = bool(
        social_info["urgency"]
    )

    has_impersonation = bool(
        social_info["impersonation"]
    )

    has_promotion = bool(
        social_info["promotional"]
    )


    # --------------------------------------------------------
    # Phishing
    # --------------------------------------------------------

    if (
        has_urls
        and has_credentials
    ):

        return "PHISHING"


    # --------------------------------------------------------
    # Scam
    # --------------------------------------------------------

    if (
        has_financial
        and (
            has_urgency
            or has_urls
        )
    ):

        return "SCAM"


    # --------------------------------------------------------
    # Impersonation
    # --------------------------------------------------------

    if (
        has_impersonation
        and (
            has_urls
            or has_credentials
        )
    ):

        return "IMPERSONATION"


    # --------------------------------------------------------
    # Promotional
    # --------------------------------------------------------

    if (
        has_promotion
        and spam_probability >= 0.50
    ):

        return "PROMOTIONAL"


    # --------------------------------------------------------
    # General spam
    # --------------------------------------------------------

    if spam_probability >= 0.50:

        return "SPAM"


    return "SAFE"


# ============================================================
# RISK SCORE ENGINE
# ============================================================

def calculate_risk(
    spam_probability,
    url_info,
    social_info,
    features
):

    risk = (
        spam_probability
        * 100
    )


    # URLs

    if url_info["count"]:

        risk += min(
            url_info["count"] * 6,
            18
        )


    # URL shorteners

    if url_info["shorteners"]:

        risk += 8


    # Risky TLD

    if url_info["risky_tlds"]:

        risk += 10


    # IP URL

    if url_info["ip_urls"]:

        risk += 15


    # Suspicious structure

    if url_info[
        "suspicious_structure"
    ]:

        risk += 8


    # Urgency

    if social_info["urgency"]:

        risk += min(
            len(
                social_info["urgency"]
            ) * 4,
            12
        )


    # Financial

    if social_info["financial"]:

        risk += min(
            len(
                social_info["financial"]
            ) * 3,
            10
        )


    # Credentials

    if social_info["credentials"]:

        risk += min(
            len(
                social_info["credentials"]
            ) * 5,
            15
        )


    # Impersonation

    if social_info["impersonation"]:

        risk += 6


    # Excessive exclamation marks

    if features[
        "exclamations"
    ] >= 3:

        risk += 3


    # Excessive uppercase

    if features[
        "uppercase_ratio"
    ] >= 45:

        risk += 3


    # Numeric-heavy message

    if features[
        "digits"
    ] >= 8:

        risk += 2


    return max(
        0,
        min(
            round(risk),
            100
        )
    )


# ============================================================
# SEVERITY
# ============================================================

def risk_severity(
    score
):

    if score >= 85:

        return "CRITICAL"

    if score >= 65:

        return "HIGH"

    if score >= 40:

        return "MODERATE"

    if score >= 20:

        return "LOW"

    return "SAFE"


# ============================================================
# RECOMMENDATION ENGINE
# ============================================================

def build_recommendation(
    threat_type,
    risk_score
):

    if threat_type == "PHISHING":

        return (
            "Do not click links or submit "
            "credentials. Verify the organization "
            "through its official website or app."
        )


    if threat_type == "SCAM":

        return (
            "Do not send money, OTPs, PINs, "
            "CVVs or banking information. "
            "Verify the request independently."
        )


    if threat_type == "IMPERSONATION":

        return (
            "The message may be pretending to "
            "represent a trusted organization. "
            "Contact the organization using "
            "an official channel."
        )


    if threat_type in {
        "SPAM",
        "PROMOTIONAL"
    }:

        return (
            "Avoid replying or interacting with "
            "suspicious offers. If unsolicited, "
            "consider reporting or blocking "
            "the sender."
        )


    if risk_score < 20:

        return (
            "No major threat indicators were "
            "detected. Still verify unexpected "
            "requests before acting."
        )


    return (
        "Treat this message cautiously and "
        "verify its source before taking action."
    )


# ============================================================
# HOME / HEALTH
# ============================================================

@app.route("/")
def home():

    return jsonify({

        "message":
            "SPAMSHIELD AI API is running",

        "status":
            "success",

        "engine":
            ENGINE_MODE,

        "version":
            "1.0"
    })


@app.route("/health")
def health():

    model_loaded = (
        bundle is not None
        or (
            legacy_model is not None
            and legacy_vectorizer is not None
        )
    )


    return jsonify({

        "status":
            "healthy"
            if model_loaded
            else "degraded",

        "engine":
            ENGINE_MODE,

        "model_loaded":
            model_loaded
    })


# ============================================================
# MODEL INFORMATION
# ============================================================

@app.route("/model-info")
def model_info():

    if metadata:

        return jsonify(
            metadata
        )


    return jsonify({

        "platform":
            "SPAMSHIELD AI",

        "engine":
            ENGINE_MODE,

        "version":
            "1.0"
    })


# ============================================================
# MODEL BENCHMARK METADATA
# ============================================================

def normalize_model_metadata(raw_metadata):
    """
    Return a frontend-safe representation of model_metadata.json.
    Training metrics remain the real values produced by train_model.py.
    """
    if not isinstance(raw_metadata, dict):
        return {"models": [], "best_model": None}

    source = (
        raw_metadata.get("models")
        or raw_metadata.get("model_metrics")
        or raw_metadata.get("benchmark")
        or raw_metadata.get("results")
        or raw_metadata.get("metrics")
        or {}
    )

    models = []

    if isinstance(source, list):
        for index, item in enumerate(source):
            if not isinstance(item, dict):
                continue

            models.append({
                "name": (
                    item.get("model")
                    or item.get("name")
                    or item.get("model_name")
                    or f"Model {index + 1}"
                ),
                "accuracy": item.get("accuracy", item.get("Accuracy")),
                "precision": item.get("precision", item.get("Precision")),
                "recall": item.get("recall", item.get("Recall")),
                "f1": (
                    item.get("f1")
                    if item.get("f1") is not None
                    else item.get("f1_score")
                    if item.get("f1_score") is not None
                    else item.get("F1")
                    if item.get("F1") is not None
                    else item.get("F1_score")
                )
            })

    elif isinstance(source, dict):
        for name, item in source.items():
            if not isinstance(item, dict):
                continue

            models.append({
                "name": str(name),
                "accuracy": item.get("accuracy", item.get("Accuracy")),
                "precision": item.get("precision", item.get("Precision")),
                "recall": item.get("recall", item.get("Recall")),
                "f1": (
                    item.get("f1")
                    if item.get("f1") is not None
                    else item.get("f1_score")
                    if item.get("f1_score") is not None
                    else item.get("F1")
                    if item.get("F1") is not None
                    else item.get("F1_score")
                )
            })

    best_model = (
        raw_metadata.get("best_model")
        or raw_metadata.get("best_model_name")
        or raw_metadata.get("selected_model")
    )

    if best_model is None:
        for item in models:
            if item.get("best") is True or item.get("selected") is True:
                best_model = item["name"]
                break

    result = dict(raw_metadata)
    result["models"] = models
    result["best_model"] = best_model
    result.setdefault("platform", "SPAMSHIELD AI")
    result.setdefault("engine", ENGINE_MODE)

    if isinstance(bundle, dict):
        result.setdefault(
            "model_version",
            bundle.get("version", "SPAMSHIELD-AI-1.0")
        )
    else:
        result.setdefault("model_version", "legacy")

    return result


@app.route("/model-metadata", methods=["GET"])
def model_metadata():
    """
    Read-only endpoint for the SPAMSHIELD AI Model Center.

    The endpoint exposes training/benchmark metadata only. It does not
    expose model pickle contents or other private server files.
    """
    if not metadata:
        return jsonify({
            "error": (
                "Model metadata is unavailable. "
                "Run train_model.py first."
            ),
            "engine": ENGINE_MODE
        }), 503

    return jsonify(normalize_model_metadata(metadata))


# ============================================================
# MAIN PREDICTION API
# ============================================================

@app.route(
    "/predict",
    methods=["POST"]
)
def predict():

    try:

        # ----------------------------------------------------
        # Read request
        # ----------------------------------------------------

        data = request.get_json(
            silent=True
        )


        if not data:

            return jsonify({

                "error":
                    "JSON body is required"

            }), 400


        message = data.get(
            "message",
            ""
        )


        # ----------------------------------------------------
        # Validate message
        # ----------------------------------------------------

        if not isinstance(
            message,
            str
        ):

            return jsonify({

                "error":
                    "Message must be text"

            }), 400


        message = message.strip()


        if not message:

            return jsonify({

                "error":
                    "Message cannot be empty"

            }), 400


        if len(message) > 20000:

            return jsonify({

                "error":
                    "Message exceeds 20,000 characters"

            }), 400


        # ----------------------------------------------------
        # Optional metadata from frontend
        # ----------------------------------------------------

        source = data.get(
            "source",
            "Unknown"
        )

        sender = data.get(
            "sender",
            ""
        )


        # ----------------------------------------------------
        # MACHINE LEARNING
        # ----------------------------------------------------

        if ENGINE_MODE == "ensemble":

            ml_result = run_ensemble(
                message
            )

        elif ENGINE_MODE == "legacy":

            ml_result = run_legacy(
                message
            )

        else:

            return jsonify({

                "error":
                    "AI model is unavailable. "
                    "Run train_model.py first."

            }), 500


        spam_probability = (
            ml_result[
                "spam_probability"
            ]
        )


        # ----------------------------------------------------
        # THREAT INTELLIGENCE
        # ----------------------------------------------------

        url_info = analyze_urls(
            message
        )

        social_info = (
            analyze_social_engineering(
                message
            )
        )

        message_features = (
            analyze_message_features(
                message
            )
        )


        # ----------------------------------------------------
        # CLASSIFICATION
        # ----------------------------------------------------

        threat_type = classify_threat(

            spam_probability,

            url_info,

            social_info
        )


        # ----------------------------------------------------
        # RISK SCORE
        # ----------------------------------------------------

        risk_score = calculate_risk(

            spam_probability,

            url_info,

            social_info,

            message_features
        )


        severity = risk_severity(
            risk_score
        )


        # ----------------------------------------------------
        # COLLECT SIGNALS
        # ----------------------------------------------------

        signals = []


        signals.extend(
            url_info["signals"]
        )

        signals.extend(
            social_info["signals"]
        )


        if (
            message_features[
                "uppercase_ratio"
            ] >= 45
        ):

            signals.append(
                "Unusually high uppercase usage"
            )


        if (
            message_features[
                "exclamations"
            ] >= 3
        ):

            signals.append(
                "Excessive exclamation marks"
            )


        if (
            message_features[
                "digits"
            ] >= 8
        ):

            signals.append(
                "High numeric content"
            )


        # Remove duplicates

        signals = list(
            dict.fromkeys(
                signals
            )
        )


        # ----------------------------------------------------
        # RECOMMENDATION
        # ----------------------------------------------------

        recommendation = (
            build_recommendation(
                threat_type,
                risk_score
            )
        )


        # ----------------------------------------------------
        # SPAM / HAM
        # ----------------------------------------------------

        is_spam = (
            spam_probability >= 0.50
        )


        # ----------------------------------------------------
        # FINAL RESPONSE
        # ----------------------------------------------------

        response = {

            # Original API fields
            "result":
                "spam"
                if is_spam
                else "ham",

            "confidence":
                ml_result[
                    "confidence"
                ],


            # SPAMSHIELD AI
            "risk_score":
                risk_score,

            "severity":
                severity,

            "classification":
                threat_type,


            # Source information
            "source":
                source,

            "sender":
                sender,


            # Threat signals
            "signals":
                signals,

            "signal_count":
                len(signals),


            # Recommendation
            "recommendation":
                recommendation,


            # URL intelligence
            "urls":
                url_info,


            # Message intelligence
            "message_features":
                message_features,


            # Social engineering
            "social_engineering":
                social_info,


            # Individual model results
            "model_scores":
                ml_result[
                    "model_scores"
                ],


            # Engine information
            "engine":
                ENGINE_MODE,

            "model_version":
                (
                    bundle.get(
                        "version",
                        "SPAMSHIELD-AI-1.0"
                    )
                    if bundle
                    else "legacy"
                )
        }


        return jsonify(
            response
        )


    except Exception as error:

        print(
            "Prediction error:",
            error
        )


        return jsonify({

            "error":
                "An internal analysis error occurred.",

            "details":
                str(error)

        }), 500


# ============================================================
# LOCAL SERVER
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )


    app.run(

        host="0.0.0.0",

        port=port,

        debug=False
    )
