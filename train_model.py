import pandas as pd
import pickle

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score


# ==========================================
# 1. LOAD DATASET
# ==========================================

data = pd.read_csv(
    "../dataset/spam.csv",
    sep="\t",
    header=None,
    names=["label", "message"],
    encoding="latin-1"
)


print("Dataset loaded successfully!")
print("Total messages:", len(data))


# ==========================================
# 2. CLEAN DATA
# ==========================================

data = data[["label", "message"]]

data.dropna(inplace=True)


# ==========================================
# 3. INPUT AND OUTPUT
# ==========================================

X = data["message"]

y = data["label"]


# ==========================================
# 4. CONVERT TEXT INTO NUMBERS
#    Using TF-IDF
# ==========================================

vectorizer = TfidfVectorizer(
    lowercase=True,
    stop_words="english",
    max_features=5000
)


X_vectorized = vectorizer.fit_transform(X)


# ==========================================
# 5. SPLIT DATA
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X_vectorized,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


# ==========================================
# 6. CREATE MACHINE LEARNING MODEL
# ==========================================

model = MultinomialNB()


# ==========================================
# 7. TRAIN MODEL
# ==========================================

print("Training model...")

model.fit(X_train, y_train)


# ==========================================
# 8. TEST MODEL
# ==========================================

predictions = model.predict(X_test)


accuracy = accuracy_score(
    y_test,
    predictions
)


print()
print("===================================")
print("MODEL TRAINING COMPLETED")
print("===================================")

print(
    "Model Accuracy:",
    round(accuracy * 100, 2),
    "%"
)


# ==========================================
# 9. SAVE MODEL
# ==========================================

with open("model.pkl", "wb") as file:

    pickle.dump(model, file)


# ==========================================
# 10. SAVE VECTORIZER
# ==========================================

with open("vectorizer.pkl", "wb") as file:

    pickle.dump(vectorizer, file)


print()
print("model.pkl created successfully!")
print("vectorizer.pkl created successfully!")
print()
print("You can now run app.py")