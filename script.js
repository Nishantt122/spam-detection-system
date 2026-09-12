/* =========================================================
   SPAMSHIELD AI — Main Frontend Logic
   ========================================================= */

const API_URL =
    "https://spam-detection-system-tk0i.onrender.com/predict";


/* =========================================================
   ELEMENTS
   ========================================================= */

const messageInput = document.getElementById("messageInput");
const detectBtn = document.getElementById("detectBtn");
const clearBtn = document.getElementById("clearBtn");
const exampleBtn = document.getElementById("exampleBtn");

const charCount = document.getElementById("charCount");

const sourceTabs = document.querySelectorAll(".source-tab");
const sourceType = document.getElementById("sourceType");

const senderInput = document.getElementById("senderInput");
const replyToInput = document.getElementById("replyToInput");
const subjectInput = document.getElementById("subjectInput");
const urlInput = document.getElementById("urlInput");

const resultSection = document.getElementById("resultSection");

const resultSeverity = document.getElementById("resultSeverity");
const resultTitle = document.getElementById("resultTitle");
const resultMessage = document.getElementById("resultMessage");
const resultIcon = document.getElementById("resultIcon");

const riskScore = document.getElementById("riskScore");
const progressBar = document.getElementById("progressBar");
const confidence = document.getElementById("confidence");

const indicatorList = document.getElementById("indicatorList");

const resultSource = document.getElementById("resultSource");
const resultDomain = document.getElementById("resultDomain");
const resultReputation = document.getElementById("resultReputation");
const resultSourceRisk = document.getElementById("resultSourceRisk");

const recommendationText =
    document.getElementById("recommendationText");

const newScanBtn = document.getElementById("newScanBtn");

const toast = document.getElementById("toast");

const mobileMenuBtn =
    document.querySelector(".mobile-menu-btn");

const mobilePanel =
    document.querySelector(".mobile-panel");


/* =========================================================
   EXAMPLE MESSAGES
   ========================================================= */

const examples = [
    {
        source: "Email",
        sender: "security@yourbank-alert.com",
        subject: "URGENT: Account Verification Required",
        message:
            "URGENT! Your bank account has been temporarily suspended. Verify your account immediately by clicking https://secure-account-verify.com/login. Failure to verify within 24 hours will result in permanent suspension."
    },

    {
        source: "SMS",
        sender: "+91 9876543210",
        message:
            "Congratulations! You have won Rs. 25,00,000 in our lucky draw. Claim your prize now by visiting http://claim-prize.example.com"
    },

    {
        source: "WhatsApp",
        sender: "Unknown Contact",
        message:
            "Hey! You have been selected for a special cash reward. Send your OTP and bank details to receive the payment immediately."
    },

    {
        source: "Social",
        sender: "Unknown Account",
        message:
            "You won! Click this link now to claim your exclusive reward before the offer expires: https://bit.ly/example"
    },

    {
        source: "Email",
        sender: "friend@example.com",
        subject: "Weekend plans",
        message:
            "Hey! Are we still meeting for coffee this weekend? Let me know what time works for you."
    }
];


/* =========================================================
   CHARACTER COUNTER
   ========================================================= */

function updateCharacterCount() {

    if (!messageInput || !charCount) return;

    charCount.textContent =
        `${messageInput.value.length.toLocaleString()} / 20,000`;
}

if (messageInput) {
    messageInput.addEventListener(
        "input",
        updateCharacterCount
    );
}

updateCharacterCount();


/* =========================================================
   SOURCE TABS
   ========================================================= */

sourceTabs.forEach(tab => {

    tab.addEventListener("click", () => {

        sourceTabs.forEach(item =>
            item.classList.remove("active")
        );

        tab.classList.add("active");

        const selectedSource =
            tab.dataset.source ||
            tab.textContent.trim();

        if (sourceType) {
            sourceType.value = selectedSource;
        }

        updateSourceFields(selectedSource);
    });
});


function updateSourceFields(source) {

    const normalized =
        source.toLowerCase();

    /*
       These fields may or may not exist depending
       on the HTML source configuration.
    */

    if (senderInput) {
        senderInput.parentElement.style.display =
            normalized === "url"
                ? "none"
                : "";
    }

    if (replyToInput) {
        replyToInput.parentElement.style.display =
            normalized === "email"
                ? ""
                : "none";
    }

    if (subjectInput) {
        subjectInput.parentElement.style.display =
            normalized === "email"
                ? ""
                : "none";
    }

    if (urlInput) {
        urlInput.parentElement.style.display =
            normalized === "url"
                ? ""
                : "";
    }
}


/* =========================================================
   CLEAR
   ========================================================= */

if (clearBtn) {

    clearBtn.addEventListener("click", () => {

        if (messageInput)
            messageInput.value = "";

        if (senderInput)
            senderInput.value = "";

        if (replyToInput)
            replyToInput.value = "";

        if (subjectInput)
            subjectInput.value = "";

        if (urlInput)
            urlInput.value = "";

        updateCharacterCount();

        hideResult();

        showToast("Scanner cleared.");
    });
}


/* =========================================================
   EXAMPLE
   ========================================================= */

if (exampleBtn) {

    exampleBtn.addEventListener("click", () => {

        const example =
            examples[
                Math.floor(
                    Math.random() * examples.length
                )
            ];

        const sourceTab =
            [...sourceTabs].find(tab => {

                const value =
                    tab.dataset.source ||
                    tab.textContent.trim();

                return value.toLowerCase() ===
                    example.source.toLowerCase();

            });

        if (sourceTab) {
            sourceTab.click();
        }

        if (messageInput)
            messageInput.value = example.message;

        if (senderInput)
            senderInput.value = example.sender || "";

        if (subjectInput)
            subjectInput.value = example.subject || "";

        updateCharacterCount();

        showToast("Example threat loaded.");
    });
}


/* =========================================================
   DETECTION
   ========================================================= */

if (detectBtn) {

    detectBtn.addEventListener(
        "click",
        analyzeMessage
    );
}


async function analyzeMessage() {

    const message =
        messageInput?.value.trim() || "";

    if (!message) {

        showToast(
            "Paste a message first."
        );

        messageInput?.focus();

        return;
    }

    if (message.length > 20000) {

        showToast(
            "Message is too long. Maximum 20,000 characters."
        );

        return;
    }


    /* Loading */

    setLoading(true);

    hideResult();


    try {

        /*
         * Your existing Flask backend expects:
         *
         * {
         *     "message": "..."
         * }
         */

        const response =
            await fetch(API_URL, {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    message: message
                })
            });


        if (!response.ok) {

            throw new Error(
                `Server returned ${response.status}`
            );
        }


        const data =
            await response.json();


        /*
         * Backend returns:
         *
         * {
         *   result: "spam" / "ham",
         *   confidence: number
         * }
         */

        displayResult(
            data,
            message
        );


    } catch (error) {

        console.error(
            "SPAMSHIELD API ERROR:",
            error
        );

        showToast(
            "Unable to connect to the AI engine. Please try again."
        );

    } finally {

        setLoading(false);
    }
}


/* =========================================================
   DISPLAY RESULT
   ========================================================= */

function displayResult(data, message) {

    if (!resultSection)
        return;


    const result =
        String(data.result || "")
            .toLowerCase();


    let modelConfidence =
        Number(data.confidence);


    /*
     * Some APIs return confidence between
     * 0 and 1, others between 0 and 100.
     */

    if (
        modelConfidence > 0 &&
        modelConfidence <= 1
    ) {
        modelConfidence *= 100;
    }

    if (!Number.isFinite(modelConfidence)) {
        modelConfidence = 0;
    }

    modelConfidence =
        Math.max(
            0,
            Math.min(
                100,
                modelConfidence
            )
        );


    const isSpam =
        result === "spam";


    /*
     * Calculate a transparent frontend
     * threat score.
     *
     * This is NOT the ML confidence.
     */

    const indicators =
        analyzeThreatSignals(message);


    let score;

    if (isSpam) {

        score =
            Math.round(
                Math.max(
                    55,
                    Math.min(
                        99,
                        modelConfidence * 0.72 +
                        indicators.score * 0.28
                    )
                )
            );

    } else {

        score =
            Math.round(
                Math.max(
                    3,
                    Math.min(
                        44,
                        (100 - modelConfidence) * 0.35 +
                        indicators.score * 0.65
                    )
                )
            );
    }


    const severity =
        getSeverity(score);


    /* Result classes */

    resultSection.classList.remove(
        "result-safe",
        "result-warning",
        "result-danger",
        "result-critical"
    );


    resultSection.classList.add(
        severity.className
    );


    /* Main result */

    if (isSpam) {

        resultTitle.textContent =
            "Potential Threat Detected";

        resultMessage.textContent =
            "The AI model classified this message as spam. Review the signals below before interacting with it.";

        resultIcon.textContent =
            "!";
    }

    else {

        resultTitle.textContent =
            "No Spam Detected";

        resultMessage.textContent =
            "The AI model classified this message as legitimate. Always verify unexpected requests independently.";

        resultIcon.textContent =
            "✓";
    }


    resultSeverity.textContent =
        severity.label;


    riskScore.textContent =
        score;


    confidence.textContent =
        `AI model confidence: ${modelConfidence.toFixed(1)}%`;


    /* Risk bar */

    requestAnimationFrame(() => {

        setTimeout(() => {

            if (progressBar) {

                progressBar.style.width =
                    `${score}%`;
            }

        }, 100);

    });


    /* Indicators */

    renderIndicators(
        indicators.signals
    );


    /* Source intelligence */

    if (resultSource) {

        resultSource.textContent =
            sourceType?.value ||
            "Message";
    }

    if (resultDomain) {

        resultDomain.textContent =
            extractDomain(message) ||
            "Not detected";
    }

    if (resultReputation) {

        resultReputation.textContent =
            "Not externally verified";
    }

    if (resultSourceRisk) {

        resultSourceRisk.textContent =
            indicators.urlCount > 0
                ? "Review required"
                : "Low signal";
    }


    /* Recommendation */

    if (recommendationText) {

        recommendationText.textContent =
            getRecommendation(
                isSpam,
                score,
                indicators
            );
    }


    /*
     * Reveal result.
     */

    resultSection.classList.add("show");


    /*
     * Smoothly bring result into view.
     */

    setTimeout(() => {

        resultSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    }, 150);


    saveHistory({
        message,
        result,
        confidence: modelConfidence,
        risk: score,
        source:
            sourceType?.value ||
            "Message",
        timestamp:
            new Date().toISOString()
    });
}


/* =========================================================
   THREAT SIGNAL ANALYSIS
   ========================================================= */

function analyzeThreatSignals(message) {

    const text =
        message.toLowerCase();


    const signals = [];


    let score = 0;


    /* ---------- URLs ---------- */

    const urls =
        message.match(
            /https?:\/\/[^\s]+|www\.[^\s]+/gi
        ) || [];


    const urlCount =
        urls.length;


    if (urlCount > 0) {

        score += 20;

        signals.push(
            `${urlCount} URL detected`
        );
    }


    /* ---------- Urgency ---------- */

    const urgencyWords = [
        "urgent",
        "immediately",
        "now",
        "hurry",
        "act now",
        "expires",
        "limited time",
        "within 24 hours",
        "last chance"
    ];


    const urgencyFound =
        urgencyWords.filter(
            word => text.includes(word)
        );


    if (urgencyFound.length) {

        score +=
            Math.min(
                20,
                urgencyFound.length * 7
            );

        signals.push(
            "Urgency language detected"
        );
    }


    /* ---------- Money ---------- */

    const moneyWords = [
        "money",
        "cash",
        "payment",
        "prize",
        "reward",
        "winner",
        "won",
        "₹",
        "rs.",
        "rupees",
        "bank"
    ];


    const moneyFound =
        moneyWords.filter(
            word => text.includes(word)
        );


    if (moneyFound.length) {

        score += 15;

        signals.push(
            "Financial language detected"
        );
    }


    /* ---------- Credentials ---------- */

    const credentialWords = [
        "password",
        "otp",
        "pin",
        "cvv",
        "verification",
        "verify your account",
        "login",
        "username",
        "credentials"
    ];


    const credentialFound =
        credentialWords.filter(
            word => text.includes(word)
        );


    if (credentialFound.length) {

        score += 22;

        signals.push(
            "Credential request detected"
        );
    }


    /* ---------- Threats ---------- */

    const threatWords = [
        "blocked",
        "suspended",
        "closed",
        "legal action",
        "penalty",
        "arrest",
        "account will be closed"
    ];


    const threatFound =
        threatWords.filter(
            word => text.includes(word)
        );


    if (threatFound.length) {

        score += 15;

        signals.push(
            "Pressure or threat detected"
        );
    }


    /* ---------- Excessive punctuation ---------- */

    const exclamationCount =
        (message.match(/!/g) || []).length;


    if (exclamationCount >= 3) {

        score += 8;

        signals.push(
            "Excessive punctuation"
        );
    }


    /* ---------- ALL CAPS ---------- */

    const letters =
        message.match(/[A-Za-z]/g) || [];


    const upper =
        message.match(/[A-Z]/g) || [];


    if (
        letters.length > 12 &&
        upper.length / letters.length > 0.45
    ) {

        score += 8;

        signals.push(
            "Unusual capitalization"
        );
    }


    /* ---------- Shortened URLs ---------- */

    const shorteners = [
        "bit.ly",
        "tinyurl.com",
        "t.co",
        "goo.gl",
        "ow.ly",
        "is.gd"
    ];


    if (
        shorteners.some(
            domain =>
                text.includes(domain)
        )
    ) {

        score += 18;

        signals.push(
            "URL shortener detected"
        );
    }


    score =
        Math.min(
            100,
            score
        );


    if (!signals.length) {

        signals.push(
            "No obvious threat indicators"
        );
    }


    return {
        score,
        signals,
        urlCount,
        urgency:
            urgencyFound.length > 0,
        financial:
            moneyFound.length > 0,
        credentials:
            credentialFound.length > 0
    };
}


/* =========================================================
   SEVERITY
   ========================================================= */

function getSeverity(score) {

    if (score >= 85) {

        return {
            label: "Critical Risk",
            className: "result-critical"
        };
    }

    if (score >= 65) {

        return {
            label: "High Risk",
            className: "result-danger"
        };
    }

    if (score >= 35) {

        return {
            label: "Moderate Risk",
            className: "result-warning"
        };
    }

    return {
        label: "Low Risk",
        className: "result-safe"
    };
}


/* =========================================================
   INDICATORS UI
   ========================================================= */

function renderIndicators(signals) {

    if (!indicatorList)
        return;


    indicatorList.innerHTML = "";


    signals.forEach(signal => {

        const item =
            document.createElement("div");


        item.className =
            "indicator";


        item.textContent =
            signal;


        indicatorList.appendChild(
            item
        );
    });
}


/* =========================================================
   RECOMMENDATION
   ========================================================= */

function getRecommendation(
    isSpam,
    score,
    indicators
) {

    if (!isSpam && score < 35) {

        return (
            "The message does not show strong spam indicators. " +
            "Still avoid sharing sensitive information and verify unexpected requests independently."
        );
    }


    if (indicators.credentials) {

        return (
            "Do not share OTPs, passwords, PINs, CVVs or login credentials. " +
            "If this appears to come from an organisation, contact it through its official website or app."
        );
    }


    if (indicators.urlCount > 0) {

        return (
            "Do not click suspicious links. " +
            "Open the organisation's official website or app directly instead of using the link in the message."
        );
    }


    if (indicators.financial) {

        return (
            "Be cautious with unexpected payment, prize or financial requests. " +
            "Verify the sender independently before taking action."
        );
    }


    return (
        "Do not reply or interact until you can independently verify the sender and the request."
    );
}


/* =========================================================
   URL EXTRACTION
   ========================================================= */

function extractDomain(message) {

    const match =
        message.match(
            /https?:\/\/([^\/\s]+)/i
        );


    if (!match)
        return "";


    return match[1];
}


/* =========================================================
   LOADING
   ========================================================= */

function setLoading(isLoading) {

    if (!detectBtn)
        return;


    if (isLoading) {

        detectBtn.disabled = true;

        detectBtn.dataset.originalText =
            detectBtn.innerHTML;

        detectBtn.innerHTML =
            `<span class="loading-spinner"></span>Analyzing...`;

        detectBtn.classList.add(
            "scanning"
        );

    } else {

        detectBtn.disabled = false;

        detectBtn.innerHTML =
            detectBtn.dataset.originalText ||
            "Analyze Message";

        detectBtn.classList.remove(
            "scanning"
        );
    }
}


/* =========================================================
   HIDE RESULT
   ========================================================= */

function hideResult() {

    if (!resultSection)
        return;


    resultSection.classList.remove(
        "show",
        "result-safe",
        "result-warning",
        "result-danger",
        "result-critical"
    );


    if (progressBar) {

        progressBar.style.width =
            "0%";
    }
}


/* =========================================================
   NEW SCAN
   ========================================================= */

if (newScanBtn) {

    newScanBtn.addEventListener(
        "click",
        () => {

            hideResult();

            messageInput?.focus();

            window.scrollTo({
                top: 0,
                behavior: "smooth"
            });
        }
    );
}


/* =========================================================
   TOAST
   ========================================================= */

let toastTimer;


function showToast(message) {

    if (!toast)
        return;


    toast.textContent =
        message;


    toast.classList.add(
        "show"
    );


    clearTimeout(
        toastTimer
    );


    toastTimer =
        setTimeout(() => {

            toast.classList.remove(
                "show"
            );

        }, 2800);
}


/* =========================================================
   LOCAL HISTORY
   ========================================================= */

function saveHistory(item) {

    try {

        const history =
            JSON.parse(
                localStorage.getItem(
                    "spamshield_history"
                ) || "[]"
            );


        history.unshift(item);


        /*
         * Keep only latest 30 scans.
         */

        localStorage.setItem(
            "spamshield_history",
            JSON.stringify(
                history.slice(0, 30)
            )
        );

    } catch (error) {

        console.warn(
            "History storage unavailable."
        );
    }
}


/* =========================================================
   MOBILE MENU
   ========================================================= */

if (mobileMenuBtn) {

    mobileMenuBtn.addEventListener(
        "click",
        () => {

            mobilePanel?.classList.add(
                "active"
            );
        }
    );
}


if (mobilePanel) {

    mobilePanel.addEventListener(
        "click",
        event => {

            if (
                event.target.tagName === "A" ||
                event.target.closest(
                    ".mobile-panel-close"
                )
            ) {

                mobilePanel.classList.remove(
                    "active"
                );
            }
        }
    );
}


/* =========================================================
   ESCAPE KEY
   ========================================================= */

document.addEventListener(
    "keydown",
    event => {

        if (event.key === "Escape") {

            mobilePanel?.classList.remove(
                "active"
            );
        }
    }
);


/* =========================================================
   INITIAL SOURCE
   ========================================================= */

if (sourceTabs.length) {

    const activeTab =
        document.querySelector(
            ".source-tab.active"
        ) || sourceTabs[0];


    if (activeTab) {

        activeTab.classList.add(
            "active"
        );

        const source =
            activeTab.dataset.source ||
            activeTab.textContent.trim();


        if (sourceType) {
            sourceType.value =
                source;
        }

        updateSourceFields(
            source
        );
    }
}


/* =========================================================
   INITIAL STATE
   ========================================================= */

hideResult();
updateCharacterCount();

console.log(
    "SPAMSHIELD AI frontend initialized."
);
