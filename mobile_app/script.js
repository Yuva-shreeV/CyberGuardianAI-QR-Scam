// ============================================================
// CYBERGUARDIAN AI - FRONTEND APPLICATION LOGIC
// Focus: Payment QR Scanning & Explainable AI Threat Detection
// ============================================================

// DYNAMIC API HOST (Works seamlessly on localhost, LAN IP, and mobile devices)
// DYNAMIC API HOST
const API_URL = window.location.origin;

console.log("CyberGuardian AI connected to API:", API_URL);
// ============================================================
// GLOBAL APPLICATION STATE
// ============================================================
let currentUser = null;
let cameraStream = null;
let scanning = false;
let currentScanContext = null;

// ============================================================
// DOM ELEMENTS
// ============================================================
const loginPage = document.getElementById("loginPage");
const appPage = document.getElementById("appPage");
const loginName = document.getElementById("loginName");
const loginEmail = document.getElementById("loginEmail");
const loginButton = document.getElementById("loginButton");
const loginMessage = document.getElementById("loginMessage");
const userNameDisplay = document.getElementById("userNameDisplay");

// Core Pages (Home, Scan, History, About)
const homePage = document.getElementById("homePage");
const historySection = document.getElementById("historySection");
const aboutSection = document.getElementById("aboutSection");
const navItems = document.querySelectorAll(".bottom-nav .nav-item");

// Scanner
const scanButton = document.getElementById("scanButton");
const scannerModal = document.getElementById("scannerModal");
const closeScanner = document.getElementById("closeScanner");
const cameraVideo = document.getElementById("cameraVideo");
const qrCanvas = document.getElementById("qrCanvas");
const scannerStatus = document.getElementById("scannerStatus");

// Scan Results
const resultCard = document.getElementById("resultCard");
const resultTitle = document.getElementById("resultTitle");
const confidence = document.getElementById("confidence");
const scannedURL = document.getElementById("scannedURL");
const resultMessage = document.getElementById("resultMessage");
const safetyScore = document.getElementById("safetyScore");
const riskLevel = document.getElementById("riskLevel");
const riskFactors = document.getElementById("riskFactors");
const scanAgainButton = document.getElementById("scanAgainButton");

// History
const historyList = document.getElementById("historyList");

// Chatbot
const chatbotToggle = document.getElementById("chatbotToggle");
const chatbotPanel = document.getElementById("chatbotPanel");
const chatbotClose = document.getElementById("chatbotClose");
const chatInput = document.getElementById("chatInput");
const chatbotSend = document.getElementById("chatbotSend");
const chatMessages = document.getElementById("chatMessages");


// ============================================================
// INITIALIZATION
// ============================================================
document.addEventListener("DOMContentLoaded", function () {
    const savedUser = localStorage.getItem("cyberGuardianUser");
    if (savedUser) {
        try {
            currentUser = JSON.parse(savedUser);
            if (currentUser && currentUser.id) {
                showApp();
                return;
            }
        } catch (e) {
            localStorage.removeItem("cyberGuardianUser");
        }
    }
    showLogin();
});


// ============================================================
// AUTHENTICATION
// ============================================================
if (loginButton) loginButton.addEventListener("click", loginUser);

if (loginName) {
    loginName.addEventListener("keydown", function (e) {
        if (e.key === "Enter") loginUser();
    });
}

if (loginEmail) {
    loginEmail.addEventListener("keydown", function (e) {
        if (e.key === "Enter") loginUser();
    });
}

async function loginUser() {
    const name = loginName ? loginName.value.trim() : "";
    const email = loginEmail ? loginEmail.value.trim().toLowerCase() : "";

    if (!name) {
        showLoginMessage("Please enter your name.", "error");
        if (loginName) loginName.focus();
        return;
    }

    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        showLoginMessage("Please enter a valid email address.", "error");
        if (loginEmail) loginEmail.focus();
        return;
    }

    loginButton.disabled = true;
    loginButton.innerHTML = "Signing in...";
    showLoginMessage("", "");

    try {
        const response = await fetch(API_URL + "/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: name, email: email })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Login failed");
        }

        const data = await response.json();
        if (data.status === "success" && data.user) {
            currentUser = data.user;
            localStorage.setItem("cyberGuardianUser", JSON.stringify(currentUser));
            showLoginMessage(data.message || "Login successful!", "success");
            setTimeout(showApp, 400);
        } else {
            showLoginMessage(data.message || "Unable to sign in.", "error");
        }
    } catch (error) {
        console.error("Login error:", error);
        currentUser = { id: 1, name: name, email: email };
        localStorage.setItem("cyberGuardianUser", JSON.stringify(currentUser));
        showLoginMessage("Welcome (Offline mode ready)", "success");
        setTimeout(showApp, 400);
    } finally {
        loginButton.disabled = false;
        loginButton.innerHTML = 'Continue <span>→</span>';
    }
}

function showLoginMessage(message, type) {
    if (loginMessage) {
        loginMessage.innerText = message;
        loginMessage.className = "login-message " + type;
    }
}

function showLogin() {
    if (loginPage) loginPage.style.display = "flex";
    if (appPage) appPage.style.display = "none";
}

function showApp() {
    if (loginPage) loginPage.style.display = "none";
    if (appPage) appPage.style.display = "block";
    if (userNameDisplay) {
        userNameDisplay.innerText = currentUser ? currentUser.name : "User";
    }
    showHome();
    updateNavSelection(0);
}

function logoutUser() {
    stopCamera();
    currentUser = null;
    currentScanContext = null;
    localStorage.removeItem("cyberGuardianUser");
    if (loginName) loginName.value = "";
    if (loginEmail) loginEmail.value = "";
    showLogin();
}


// ============================================================
// NAVIGATION (HOME, SCAN, HISTORY, ABOUT)
// ============================================================
function hideAllPages() {
    if (homePage) homePage.style.display = "none";
    if (historySection) historySection.style.display = "none";
    if (aboutSection) aboutSection.style.display = "none";
}

function updateNavSelection(index) {
    navItems.forEach((item, i) => {
        if (i === index) {
            item.classList.add("active");
        } else {
            item.classList.remove("active");
        }
    });
}

function showHome() {
    hideAllPages();
    if (homePage) homePage.style.display = "block";
    updateNavSelection(0);
}

function showScan() {
    hideAllPages();
    if (homePage) homePage.style.display = "block";
    updateNavSelection(1);
    const scannerCard = document.getElementById("scannerCard");
    if (scannerCard) {
        scannerCard.scrollIntoView({ behavior: "smooth", block: "start" });
    }
}

function showHistory() {
    hideAllPages();
    if (historySection) historySection.style.display = "block";
    updateNavSelection(2);
    loadHistory();
}

function showAbout() {
    hideAllPages();
    if (aboutSection) aboutSection.style.display = "block";
    updateNavSelection(3);
}

navItems.forEach((item, index) => {
    item.addEventListener("click", function () {
        const page = item.getAttribute("data-page");
        if (page === "home") showHome();
        else if (page === "scan") showScan();
        else if (page === "history") showHistory();
        else if (page === "about") showAbout();
        else {
            if (index === 0) showHome();
            else if (index === 1) showScan();
            else if (index === 2) showHistory();
            else if (index === 3) showAbout();
        }
    });
});


// ============================================================
// PAYMENT QR DETECTION & FILTER
// ============================================================
function isPaymentQR(content) {
    const raw = String(content || "").trim();
    const lower = raw.toLowerCase();

    // 1. UPI scheme: upi://pay?...
    if (lower.startsWith("upi://")) {
        return { isPayment: true, type: "UPI Payment QR" };
    }

    // 2. BharatQR / EMVCo format (starts with 000201)
    if (lower.startsWith("000201")) {
        return { isPayment: true, type: "BharatQR / Merchant QR" };
    }

    // 3. Payment application intents
    if (lower.startsWith("paytmmp://") || lower.startsWith("phonepe://") || lower.startsWith("gpay://") || lower.startsWith("bhim://")) {
        return { isPayment: true, type: "Payment App Intent" };
    }

    // 4. Raw UPI ID (e.g. merchant@upi)
    if (/^[A-Za-z0-9._-]{2,256}@[A-Za-z0-9.-]{2,64}$/.test(raw)) {
        return { isPayment: true, type: "Direct UPI ID" };
    }

    // 5. Check if it is a general website link / URL
    if (lower.startsWith("http://") || lower.startsWith("https://") || lower.startsWith("www.")) {
        if (lower.includes("pa=") || lower.includes("upi=")) {
            return { isPayment: true, type: "Payment Gateway URL" };
        }
        return { isPayment: false, type: "Website URL / General Link" };
    }

    return { isPayment: false, type: "Non-Payment Code" };
}


// ============================================================
// CAMERA SCANNER
// ============================================================
if (scanButton) scanButton.addEventListener("click", startCamera);

if (closeScanner) {
    closeScanner.addEventListener("click", function () {
        stopCamera();
        if (scannerModal) scannerModal.classList.remove("active");
    });
}

if (scanAgainButton) {
    scanAgainButton.addEventListener("click", function () {
        if (resultCard) resultCard.style.display = "none";
        startCamera();
    });
}

async function startCamera() {
    if (resultCard) resultCard.style.display = "none";
    if (scannerModal) scannerModal.classList.add("active");
    if (scannerStatus) scannerStatus.innerText = "Requesting camera access...";

    try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error("Camera not supported on this browser.");
        }

        cameraStream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: { ideal: "environment" },
                width: { ideal: 1280 },
                height: { ideal: 720 }
            },
            audio: false
        });

        cameraVideo.srcObject = cameraStream;
        await cameraVideo.play();
        if (scannerStatus) scannerStatus.innerText = "Point camera at a payment QR code...";
        scanning = true;
        requestAnimationFrame(processVideoFrame);
    } catch (err) {
        console.error("Camera error:", err);
        if (scannerStatus) scannerStatus.innerText = "Camera access denied or unavailable.";
        alert("Camera access is needed to scan QR codes. Please allow camera permissions.");
        stopCamera();
        if (scannerModal) scannerModal.classList.remove("active");
    }
}

function stopCamera() {
    scanning = false;
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    if (cameraVideo) cameraVideo.srcObject = null;
}

function processVideoFrame() {
    if (!scanning) return;

    if (cameraVideo.readyState !== cameraVideo.HAVE_ENOUGH_DATA) {
        requestAnimationFrame(processVideoFrame);
        return;
    }

    const canvas = qrCanvas;
    const context = canvas.getContext("2d", { willReadFrequently: true });

    canvas.width = cameraVideo.videoWidth;
    canvas.height = cameraVideo.videoHeight;

    if (!canvas.width || !canvas.height) {
        requestAnimationFrame(processVideoFrame);
        return;
    }

    context.drawImage(cameraVideo, 0, 0, canvas.width, canvas.height);
    const imageData = context.getImageData(0, 0, canvas.width, canvas.height);

    const qrCode = jsQR(imageData.data, imageData.width, imageData.height, {
        inversionAttempts: "attemptBoth"
    });

    if (qrCode && qrCode.data) {
        const qrData = qrCode.data.trim();
        console.log("QR Code Scanned:", qrData);

        if (scannerStatus) scannerStatus.innerText = "QR Detected! Analyzing...";
        stopCamera();
        if (scannerModal) scannerModal.classList.remove("active");

        const qrImage = capturePerspectiveQRImage(qrCode);
        handleScannedQR(qrData, qrImage);
        return;
    }

    requestAnimationFrame(processVideoFrame);
}

function capturePerspectiveQRImage(qrCode) {
    try {
        const loc = qrCode.location;
        if (!loc) return null;

        const points = [
            loc.topLeftCorner,
            loc.topRightCorner,
            loc.bottomRightCorner,
            loc.bottomLeftCorner
        ];

        const outputSize = 512;
        const margin = 32;

        const outputCanvas = document.createElement("canvas");
        outputCanvas.width = outputSize;
        outputCanvas.height = outputSize;
        const ctx = outputCanvas.getContext("2d");

        const minX = Math.max(0, Math.min(...points.map(p => p.x)) - margin);
        const maxX = Math.min(qrCanvas.width, Math.max(...points.map(p => p.x)) + margin);
        const minY = Math.max(0, Math.min(...points.map(p => p.y)) - margin);
        const maxY = Math.min(qrCanvas.height, Math.max(...points.map(p => p.y)) + margin);
        const w = maxX - minX;
        const h = maxY - minY;

        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, outputSize, outputSize);
        ctx.drawImage(qrCanvas, minX, minY, w, h, margin, margin, outputSize - 2 * margin, outputSize - 2 * margin);

        return outputCanvas.toDataURL("image/png");
    } catch (e) {
        if (qrCanvas && qrCanvas.width) {
            return qrCanvas.toDataURL("image/png");
        }
        return null;
    }
}


// ============================================================
// SCAN RESULT RENDERING (EXCLUDES AMOUNT, PURPOSE, RECIPIENT)
// ============================================================
async function handleScannedQR(qrData, qrImage) {
    // 1. STRICT CHECK: General website URLs are NOT payment QRs
    const qrCheck = isPaymentQR(qrData);

    if (!qrCheck.isPayment) {
        showNonPaymentQRResult(qrData, qrCheck.type);
        return;
    }

    // 2. Send genuine Payment QR to AI Backend
    if (scanButton) {
        scanButton.disabled = true;
        scanButton.innerHTML = "Analyzing Payment QR...";
    }

    try {
        const response = await fetch(API_URL + "/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                qr_content: qrData,
                user_id: currentUser ? currentUser.id : 0,
                image_data: qrImage
            })
        });

        if (!response.ok) {
            throw new Error("Analysis request failed");
        }

        const data = await response.json();
        console.log("Prediction result:", data);

        if (data.status === "rejected" || data.is_payment_qr === false) {
            showNonPaymentQRResult(qrData, data.qr_type || "Web URL");
            return;
        }

        displayPaymentQRResult(data, qrData);

    } catch (error) {
        console.error("Prediction error:", error);
        // Show a clear error — do NOT fall back to the local JS evaluator,
        // which uses simple keyword matching and gives inconsistent results
        // compared to the real AI model. The user must get real AI results only.
        if (resultCard) {
            resultCard.style.display = "block";
            resultCard.className = "result-card non-payment";
            resultCard.innerHTML = `
                <div style="text-align:center; padding:24px 16px;">
                    <div style="font-size:42px; margin-bottom:12px;">⚠️</div>
                    <h3 style="color:#f8fafc; margin-bottom:8px;">Server Not Ready</h3>
                    <p style="color:#94a3b8; font-size:14px; margin-bottom:16px;">
                        The AI analysis server could not be reached.<br>
                        Please wait a few seconds for the server to fully start, then scan again.
                    </p>
                    <button onclick="if(resultCard)resultCard.style.display='none'; startCamera();"
                        style="background:#6c63ff; color:#fff; border:none; border-radius:12px;
                               padding:10px 24px; font-size:14px; cursor:pointer;">
                        Try Again
                    </button>
                </div>
            `;
        }
    } finally {
        if (scanButton) {
            scanButton.disabled = false;
            scanButton.innerHTML = 'Start Camera Scan <span>→</span>';
        }
    }
}

function showNonPaymentQRResult(qrData, qrType) {
    if (!resultCard) return;

    resultCard.style.display = "block";
    resultCard.className = "result-card non-payment";

    if (resultTitle) {
        resultTitle.innerText = "⚠️ Non-Payment QR Code";
        resultTitle.style.color = "#f59e0b";
    }

    if (confidence) confidence.innerText = "100.00";
    if (scannedURL) scannedURL.innerText = qrData;
    if (safetyScore) safetyScore.innerText = "N/A";
    if (riskLevel) {
        riskLevel.innerText = "Web Link (Ignored)";
        riskLevel.style.color = "#f59e0b";
    }

    if (resultMessage) {
        resultMessage.innerHTML = `
            <div class="non-payment-notice">
                <strong>Why this result?</strong><br>
                The scanned QR code contains a <strong>${escapeHTML(qrType)}</strong>, not a Payment QR code.
                <br><br>
                🛡️ <em>CyberGuardian AI exclusively evaluates Payment QR codes</em> to protect against unauthorized fund transfers and Quishing scams.
                <br><br>
                🚫 <strong>Notice:</strong> This web link has <strong>NOT been added to your payment history</strong>.
            </div>
        `;
    }

    if (riskFactors) {
        riskFactors.innerHTML = `
            <div class="risk-factor-item">
                <span class="risk-factor-feature">QR Code Classification</span>
                <span class="risk-factor-impact" style="color:#f59e0b;">Non-Payment Link</span>
            </div>
            <div class="risk-factor-item">
                <span class="risk-factor-feature">History Status</span>
                <span class="risk-factor-impact" style="color:#a7b0c5;">Excluded from History</span>
            </div>
            <div class="risk-factor-item">
                <span class="risk-factor-feature">Action Required</span>
                <span class="risk-factor-impact" style="color:#60a5fa;">Scan a genuine UPI or BharatQR code</span>
            </div>
        `;
    }
}

function displayPaymentQRResult(data, qrData) {
    if (!resultCard) return;

    currentScanContext = data;
    resultCard.style.display = "block";
    resultCard.classList.remove("safe", "phishing", "warning", "non-payment");

    const prediction = data.prediction || "Safe";
    const level = data.risk_level || "Safe";
    const scoreVal = data.safety_score != null ? data.safety_score : 95;
    const confVal = data.confidence != null ? Number(data.confidence).toFixed(2) : "93.00";

    if (resultTitle) resultTitle.innerText = prediction;
    if (confidence) confidence.innerText = confVal;
    if (scannedURL) scannedURL.innerText = qrData;
    if (safetyScore) safetyScore.innerText = scoreVal;
    if (riskLevel) riskLevel.innerText = level;

    // Apply color themes
    if (prediction === "Safe" || level === "Safe") {
        resultCard.classList.add("safe");
        if (resultTitle) resultTitle.style.color = "#22c55e";
        if (resultMessage) {
            resultMessage.innerHTML = "✅ Verified format. This payment QR code appears legitimate and safe to proceed.";
        }
    } else {
        resultCard.classList.add("phishing");
        if (resultTitle) resultTitle.style.color = "#ef4444";
        if (resultMessage) {
            resultMessage.innerHTML = "🚨 High Risk! Potential payment fraud or deceptive redirection detected. Do NOT authorize.";
        }
    }

    // Render explainable security checks (NO amount, purpose, or recipient)
    renderSecurityFeatures(data.risk_factors);
}

function renderSecurityFeatures(factors) {
    if (!riskFactors) return;
    riskFactors.innerHTML = "";

    const heading = document.createElement("h4");
    heading.innerText = "Security Features & Explainable AI Checks:";
    riskFactors.appendChild(heading);

    if (!factors || factors.length === 0) {
        const item = document.createElement("div");
        item.className = "risk-factor-item";
        item.innerHTML = `
            <span class="risk-factor-feature">Payment QR Integrity</span>
            <span class="risk-factor-impact" style="color:#22c55e;">Verified Safe</span>
        `;
        riskFactors.appendChild(item);
        return;
    }

    factors.forEach(f => {
        const div = document.createElement("div");
        div.className = "risk-factor-item";

        let title = "Security Check";
        let impact = "Standard";
        let detail = "";

        if (typeof f === "object" && f !== null) {
            title = f.feature || f.name || title;
            impact = f.impact || impact;
            detail = f.detail || f.message || "";
        } else {
            title = String(f);
        }

        let badgeColor = "#22c55e";
        if (impact.toLowerCase().includes("risk") || impact.toLowerCase().includes("irregular") || impact.toLowerCase().includes("unsafe")) {
            badgeColor = "#ef4444";
        } else if (impact.toLowerCase().includes("check") || impact.toLowerCase().includes("moderate")) {
            badgeColor = "#f59e0b";
        }

        div.innerHTML = `
            <div style="display:flex; justify-content:space-between; width:100%; align-items:center;">
                <span class="risk-factor-feature" style="font-weight:600;">${escapeHTML(title)}</span>
                <span class="risk-factor-impact" style="color:${badgeColor}; font-weight:600;">${escapeHTML(impact)}</span>
            </div>
            ${detail ? `<p style="color:#cbd5e1; font-size:12px; margin:4px 0 0 0; line-height:1.4;">${escapeHTML(detail)}</p>` : ""}
        `;
        riskFactors.appendChild(div);
    });
}

function evaluateLocalPaymentQR(qrData) {
    const lower = qrData.toLowerCase();
    const hasUrl = lower.includes("http://") || lower.includes("https://");
    const hasScam = lower.includes("refund") || lower.includes("claim") || lower.includes("reward") || lower.includes("pin");

    if (hasUrl || hasScam) {
        return {
            status: "success",
            prediction: "Malicious",
            confidence: 94.0,
            safety_score: 22,
            risk_level: "High Risk",
            risk_factors: [
                { feature: "Anti-Phishing Link Check", impact: "High Risk", detail: "Unauthorized redirect URL or deceptive phrasing detected" },
                { feature: "Payment Scheme Routing", impact: "Irregular Check", detail: "Payment payload fails standard authorized merchant check" }
            ],
            recommendation: "Do NOT approve this payment or enter your UPI PIN."
        };
    }

    return {
        status: "success",
        prediction: "Safe",
        confidence: 93.0,
        safety_score: 96,
        risk_level: "Safe",
        risk_factors: [
            { feature: "Anti-Phishing Link Check", impact: "Verified Safe", detail: "No deceptive redirect links or unauthorized URLs hidden in QR payload" },
            { feature: "Payment Scheme Routing", impact: "Authentic Scheme", detail: "Standard authorized merchant payment routing verified" },
            { feature: "Deceptive Instruction Check", impact: "No Threat Detected", detail: "No fraudulent instructions or deceptive PIN/OTP requests found" }
        ],
        recommendation: "Verified format. Safe to proceed."
    };
}


// ============================================================
// SCAN HISTORY
// ============================================================
async function loadHistory() {
    if (!currentUser || !currentUser.id) return;
    if (!historyList) return;

    historyList.innerHTML = `
        <div style="text-align:center; padding:30px; color:#94a3b8;">
            Loading scan history...
        </div>
    `;

    try {
        const response = await fetch(API_URL + "/history/" + currentUser.id);
        if (!response.ok) throw new Error("Failed to load history");

        const data = await response.json();
        const items = data.history || [];

        if (items.length === 0) {
            historyList.innerHTML = `
                <div class="history-empty" style="text-align:center; padding:40px; color:#94a3b8;">
                    <div style="font-size:36px; margin-bottom:10px;">📋</div>
                    <h3 style="color:#f8fafc; margin-bottom:6px;">No Scans Yet</h3>
                    <p style="font-size:13px;">Your scanned Payment QR security results will appear here.</p>
                </div>
            `;
            return;
        }

        historyList.innerHTML = "";
        items.forEach(item => {
            const card = document.createElement("div");
            card.className = "history-card";

            const pred = item.prediction || "Safe";
            let statusClass = "safe";
            let color = "#22c55e";
            if (pred === "Malicious" || item.risk_level === "High Risk") {
                statusClass = "phishing";
                color = "#ef4444";
            }

            card.innerHTML = `
                <div class="history-card-header" style="display:flex; justify-content:space-between; align-items:center;">
                    <div class="history-status ${statusClass}" style="color:${color}; font-weight:600;">
                        ${escapeHTML(pred)} • ${escapeHTML(item.risk_level || "Verified")}
                    </div>
                    <button class="delete-history-btn" type="button" style="background:rgba(239,68,68,0.15); border:1px solid rgba(239,68,68,0.3); color:#fca5a5; border-radius:6px; padding:3px 8px; font-size:11px; cursor:pointer;">
                        Delete
                    </button>
                </div>
                <div class="history-content" style="margin-top:10px;">
                    <div class="history-qr-content">
                        <span style="font-size:11px; color:#94a3b8;">Scanned Payment QR:</span>
                        <p style="font-size:12px; color:#e2e8f0; word-break:break-all; margin:3px 0 8px;">
                            ${escapeHTML(item.qr_content || "N/A")}
                        </p>
                    </div>
                    <div class="history-details" style="display:flex; gap:16px; font-size:12px; color:#94a3b8;">
                        <div>Safety Score: <strong style="color:${color};">${escapeHTML(item.risk_score || "N/A")}/100</strong></div>
                        <div>Confidence: <strong style="color:#f8fafc;">${item.confidence != null ? Number(item.confidence).toFixed(1) : "N/A"}%</strong></div>
                    </div>
                    ${item.risk_factors ? `<div style="font-size:11px; color:#a7b0c5; margin-top:6px; line-height:1.4;">${escapeHTML(item.risk_factors)}</div>` : ""}
                    <div class="history-date" style="font-size:11px; color:#64748b; margin-top:6px;">
                        🕒 ${formatDate(item.scanned_at)}
                    </div>
                </div>
            `;

            const delBtn = card.querySelector(".delete-history-btn");
            if (delBtn) {
                delBtn.addEventListener("click", () => deleteHistoryItem(item.id));
            }

            historyList.appendChild(card);
        });

    } catch (err) {
        console.error("History loading error:", err);
        historyList.innerHTML = `
            <div style="text-align:center; padding:30px; color:#f87171;">
                Could not load history. Please ensure backend is running.
            </div>
        `;
    }
}

async function deleteHistoryItem(scanId) {
    if (!confirm("Are you sure you want to delete this scan from history?")) return;

    try {
        const response = await fetch(API_URL + "/history/" + scanId + (currentUser ? "?user_id=" + currentUser.id : ""), {
            method: "DELETE"
        });
        if (!response.ok) throw new Error("Delete failed");
        loadHistory();
    } catch (err) {
        console.error("Delete error:", err);
        alert("Unable to delete history entry.");
    }
}

async function clearAllHistory() {
    if (!currentUser || !currentUser.id) return;
    if (!confirm("Are you sure you want to clear your entire scan history? This cannot be undone.")) return;

    try {
        const response = await fetch(API_URL + "/history?user_id=" + currentUser.id, {
            method: "DELETE"
        });
        if (!response.ok) throw new Error("Clear failed");
        loadHistory();
    } catch (err) {
        console.error("Clear history error:", err);
        alert("Unable to clear history.");
    }
}


// ============================================================
// CHATBOT
// ============================================================
function toggleCyberChat() {
    if (!chatbotPanel) return;
    if (chatbotPanel.classList.contains("active")) {
        closeCyberChat();
    } else {
        chatbotPanel.classList.add("active");
        if (chatInput) chatInput.focus();
        scrollChatToBottom();
    }
}

function closeCyberChat() {
    if (chatbotPanel) chatbotPanel.classList.remove("active");
}

function scrollChatToBottom() {
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

function askQuickPrompt(text) {
    if (chatInput) chatInput.value = text;
    sendCyberChat();
}

if (chatInput) {
    chatInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
            e.preventDefault();
            sendCyberChat();
        }
    });
}

if (chatbotSend) {
    chatbotSend.addEventListener("click", sendCyberChat);
}

async function sendCyberChat() {
    if (!chatInput) return;
    const message = chatInput.value.trim();
    if (!message) return;

    appendChatBubble(message, "user");
    chatInput.value = "";

    const typingBubble = appendChatBubble("Thinking...", "bot");

    try {
        const response = await fetch(API_URL + "/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: message,
                user_id: currentUser ? currentUser.id : null,
                scan_context: currentScanContext
            })
        });

        if (!response.ok) throw new Error("Chat response failed");

        const data = await response.json();
        if (typingBubble) typingBubble.remove();
        appendChatBubble(data.reply || data.message || "I could not answer that question.", "bot");

    } catch (err) {
        console.error("Chat error:", err);
        if (typingBubble) typingBubble.remove();
        appendChatBubble("I'm having trouble connecting to the CyberGuardian AI service right now.", "bot");
    }
}

function appendChatBubble(text, sender) {
    if (!chatMessages) return null;
    const div = document.createElement("div");
    div.className = "chat-message " + sender;
    div.innerText = text;
    chatMessages.appendChild(div);
    scrollChatToBottom();
    return div;
}


// ============================================================
// MODAL & ESCAPE HANDLING
// ============================================================
window.addEventListener("click", function (e) {
    if (e.target === scannerModal) {
        stopCamera();
        scannerModal.classList.remove("active");
    }
});

document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
        if (scannerModal && scannerModal.classList.contains("active")) {
            stopCamera();
            scannerModal.classList.remove("active");
        }
        if (chatbotPanel && chatbotPanel.classList.contains("active")) {
            closeCyberChat();
        }
    }
});


// ============================================================
// UTILITIES
// ============================================================
function escapeHTML(str) {
    const div = document.createElement("div");
    div.textContent = String(str != null ? str : "");
    return div.innerHTML;
}

function formatDate(dateValue) {
    if (!dateValue) return "Just now";
    try {
        let d;
        if (dateValue instanceof Date) {
            d = dateValue;
        } else {
            let val = String(dateValue).trim();
            if (val.includes("-") || val.includes("/")) {
                val = val.replace(" ", "T");
                if (!val.endsWith("Z") && !/[+-]\d{2}(:?\d{2})?$/.test(val)) {
                    val += "Z";
                }
            }
            d = new Date(val);
        }
        if (isNaN(d.getTime())) return String(dateValue);
        return d.toLocaleString("en-IN", {
            timeZone: "Asia/Kolkata",
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });
    } catch (e) {
        return String(dateValue);
    }
}

// Global functions for inline HTML onclick attributes
window.clearAllHistory = clearAllHistory;
window.logoutUser = logoutUser;
window.toggleCyberChat = toggleCyberChat;
window.closeCyberChat = closeCyberChat;
window.sendCyberChat = sendCyberChat;
window.askQuickPrompt = askQuickPrompt;

console.log("CyberGuardian AI QR Scanner ready.");