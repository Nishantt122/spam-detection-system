from flask import Flask, request, jsonify
from flask_cors import CORS

import pickle
import os


app = Flask(__name__)

CORS(app)


# MODEL PATHS

MODEL_PATH = "model.pkl"
VECTORIZER_PATH = "vectorizer.pkl"


model = None
vectorizer = None


# LOAD MODEL

try:

    if os.path.exists(MODEL_PATH):

        with open(MODEL_PATH, "rb") as file:
            model = pickle.load(file)

        print("ML model loaded successfully.")

    else:

        print("model.pkl not found.")

except Exception as e:

    print("Error loading model:", e)


# LOAD VECTORIZER

try:

    if os.path.exists(VECTORIZER_PATH):

        with open(VECTORIZER_PATH, "rb") as file:
            vectorizer = pickle.load(file)

        print("Vectorizer loaded successfully.")

    else:

        print("vectorizer.pkl not found.")

except Exception as e:

    print("Error loading vectorizer:", e)


# HOME ROUTE

@app.route("/")
def home():

    return jsonify({

        "message": "Spam Detection API is running",

        "status": "success"

    })


# DETECTION ROUTE

@app.route("/predict", methods=["POST"])
def predict():

    try:

        data = request.get_json()


        if not data or "message" not in data:

            return jsonify({

                "error": "Message is required"

            }), 400


        message = data["message"]


        if not message.strip():

            return jsonify({

                "error": "Message cannot be empty"

            }), 400


        # Check if ML model exists

        if model is None or vectorizer is None:

            return jsonify({

                "error": "ML model is not available. Please train the model first."

            }), 500


        # Convert message to numerical features

        transformed_message = vectorizer.transform([message])


        # Prediction

        prediction = model.predict(transformed_message)[0]


        # Probability

        probability = None


        if hasattr(model, "predict_proba"):

            probabilities = model.predict_proba(
                transformed_message
            )[0]

            probability = max(probabilities) * 100


        # Convert prediction to readable result

        prediction_string = str(prediction).lower()


        if prediction_string in ["spam", "1", "true"]:

            result = "spam"

        else:

            result = "ham"


        return jsonify({

            "result": result,

            "confidence": round(
                probability if probability else 0,
                2
            )

        })


    except Exception as e:

        return jsonify({

            "error": str(e)

        }), 500


# RUN SERVER

if __name__ == "__main__":

    app.run(

        debug=True,

        host="127.0.0.1",

        port=5000

    )