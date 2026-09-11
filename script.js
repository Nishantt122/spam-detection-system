const messageInput = document.getElementById("messageInput");

const detectBtn = document.getElementById("detectBtn");

const clearBtn = document.getElementById("clearBtn");

const charCount = document.getElementById("charCount");

const resultBox = document.getElementById("resultBox");

const resultIcon = document.getElementById("resultIcon");

const resultTitle = document.getElementById("resultTitle");

const resultMessage = document.getElementById("resultMessage");

const confidence = document.getElementById("confidence");

const progressBar = document.getElementById("progressBar");

const totalMessages = document.getElementById("totalMessages");

const spamMessages = document.getElementById("spamMessages");

const safeMessages = document.getElementById("safeMessages");

const accuracyElement = document.getElementById("accuracy");


let total = 0;

let spam = 0;

let safe = 0;


/* ================= CHARACTER COUNT ================= */

messageInput.addEventListener("input", function () {

    const length = messageInput.value.length;

    charCount.textContent = length + " characters";

});


/* ================= CLEAR ================= */

clearBtn.addEventListener("click", function () {

    messageInput.value = "";

    charCount.textContent = "0 characters";

    resultBox.classList.add("hidden");

    progressBar.style.width = "0%";

});


/* ================= DETECT BUTTON ================= */

detectBtn.addEventListener("click", function () {

    const message = messageInput.value.trim();

    if (message === "") {

        alert("Please enter a message first.");

        return;

    }

    detectSpam(message);

});


/* ================= SPAM DETECTION ================= */

async function detectSpam(message) {

    detectBtn.disabled = true;

    detectBtn.textContent = "⏳ Analyzing...";


    try {

        const response = await fetch(
         "https://spam-detection-system-tk0i.onrender.com/predict",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    message: message
                })
            }
        );


        const data = await response.json();


        if (!response.ok) {

            throw new Error(
                data.error || "Server error"
            );

        }


        const isSpam = data.result === "spam";

        const score = Math.round(data.confidence);


        total++;


        if (isSpam) {

            spam++;

        } else {

            safe++;

        }


        updateStatistics();


        showResult(
            isSpam,
            score
        );


    } catch (error) {

        console.error(error);

        alert(
            "Unable to connect to the Flask server.\n\n" +
            "Make sure this is running:\n" +
            "python app.py"
        );

    }


    detectBtn.disabled = false;

    detectBtn.textContent = "🔍 Detect Spam";

}


/* ================= SHOW RESULT ================= */

function showResult(isSpam, score) {

    resultBox.classList.remove("hidden");


    if (isSpam) {

        resultIcon.textContent = "🚨";

        resultTitle.textContent = "Spam Detected";

        resultMessage.textContent =
            "This message is classified as SPAM by the machine learning model.";

    } else {

        resultIcon.textContent = "✅";

        resultTitle.textContent = "Message Looks Safe";

        resultMessage.textContent =
            "This message is classified as a legitimate message.";

    }


    confidence.textContent = score + "%";


    progressBar.style.width = "0%";


    setTimeout(function () {

        progressBar.style.width = score + "%";

    }, 100);


    resultBox.scrollIntoView({
        behavior: "smooth",
        block: "center"
    });

}


/* ================= UPDATE STATISTICS ================= */

function updateStatistics() {

    totalMessages.textContent = total;

    spamMessages.textContent = spam;

    safeMessages.textContent = safe;

}
