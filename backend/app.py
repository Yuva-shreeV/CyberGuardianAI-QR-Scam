import os
import re
import cv2
import base64
import numpy as np
from urllib.parse import urlparse, parse_qs, unquote
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .predictor import predict
from .database import get_connection
from .chatbot import chatbot_reply

app = FastAPI(
    title="CyberGuardian AI API",
    description="Explainable AI Based Contextual Payment QR Scam Risk Assessment",
    version="2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOBILE_APP_DIR = os.path.join(BASE_DIR, "mobile_app")

if os.path.exists(MOBILE_APP_DIR):
    app.mount("/app", StaticFiles(directory=MOBILE_APP_DIR, html=True), name="mobile_app_static")


# ============================================================
# DATA MODELS
# ============================================================

class QRData(BaseModel):
    qr_content: str
    user_id: int = 0
    image_data: str | None = None


class LoginData(BaseModel):
    name: str
    email: str


class ChatData(BaseModel):
    message: str
    user_id: int | None = None
    scan_context: dict | None = None


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_user(user_id: int):
    if not user_id or user_id <= 0:
        return None
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, name, email FROM users WHERE id = %s",
            (user_id,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def detect_qr_nature(content: str) -> tuple[bool, str]:
    """
    Determine whether a QR code is a payment QR code (UPI, BharatQR, merchant payment URI)
    or a non-payment website URL/link.
    """
    raw = str(content or "").strip()
    lower = raw.lower()

    # 1. Standard UPI URI
    if lower.startswith("upi://"):
        return True, "UPI Payment QR"

    # 2. EMVCo / BharatQR payload
    if lower.startswith("000201"):
        return True, "BharatQR / Merchant Payment QR"

    # 3. Known mobile payment intent
    if any(lower.startswith(p) for p in ["paytmmp://", "phonepe://", "gpay://", "bhim://"]):
        return True, "Mobile Payment Intent QR"

    # 4. Direct UPI handle format
    if re.fullmatch(r"[A-Za-z0-9._-]{2,256}@[A-Za-z0-9.-]{2,64}", raw):
        return True, "Direct UPI ID Payment QR"

    # 5. Check if it is a website URL
    if lower.startswith("http://") or lower.startswith("https://") or lower.startswith("www."):
        # Check if URL is an online payment gateway redirect with pa= or upi=
        if "pa=" in lower or "upi=" in lower:
            return True, "Payment Gateway URL"
        return False, "Website URL"

    return False, "Non-Payment QR"


def get_recommendation(risk_level: str) -> str:
    if risk_level == "Safe":
        return (
            "✅ Verified payment format. No deceptive indicators detected. "
            "You may safely proceed in your trusted payment app."
        )
    return (
        "🚨 High Risk! Potential payment fraud or deceptive redirection detected. "
        "Do NOT approve this transaction or enter your UPI PIN or OTP."
    )


# ============================================================
# STARTUP & DB MIGRATION
# ============================================================

@app.on_event("startup")
def startup():
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(150) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NULL,
                qr_content TEXT NOT NULL,
                prediction VARCHAR(30) NOT NULL,
                confidence DECIMAL(5,2) NULL,
                risk_score INT NULL,
                risk_level VARCHAR(30) NULL,
                risk_factors TEXT NULL,
                scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.commit()
        cursor.close()
        connection.close()
    except Exception as err:
        print("Database startup check note:", err)


# ============================================================
# HOME & HEALTH
# ============================================================

@app.get("/")
def home(request: Request):
    accept = request.headers.get("accept", "")
    index_file = os.path.join(MOBILE_APP_DIR, "index.html")
    if "text/html" in accept and os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "message": "CyberGuardian AI Backend Running",
        "status": "active",
        "version": "2.0",
        "app_url": "/app/"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "server": "CyberGuardian AI API",
        "version": "2.0"
    }


# ============================================================
# USER AUTHENTICATION
# ============================================================

@app.post("/login")
def login_user(data: LoginData):
    name = data.name.strip()
    email = data.email.strip().lower()

    if not name:
        raise HTTPException(status_code=400, detail="Name is required.")

    if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")

    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT id, name, email FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user:
            return {
                "status": "success",
                "message": f"Welcome back, {user['name']}!",
                "user": user
            }

        cursor.execute("INSERT INTO users (name, email) VALUES (%s, %s)", (name, email))
        connection.commit()
        user_id = cursor.lastrowid

        return {
            "status": "success",
            "message": "Account created successfully!",
            "user": {"id": user_id, "name": name, "email": email}
        }
    except Exception as error:
        if connection:
            connection.rollback()
        print("Login DB error:", error)
        raise HTTPException(status_code=500, detail="Database error during login.")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ============================================================
# QR PREDICTION (ONLY PAYMENT QR SCANNING)
# ============================================================

@app.post("/predict")
def predict_qr(data: QRData):
    qr_content = data.qr_content.strip()

    if not qr_content:
        raise HTTPException(status_code=400, detail="QR content is empty.")

    # 1. STRICT REQUIREMENT: Only payment QRs are accepted.
    # Non-payment website URLs are rejected and NOT saved to history.
    is_payment, qr_type = detect_qr_nature(qr_content)

    if not is_payment:
        return {
            "status": "rejected",
            "is_payment_qr": False,
            "qr_type": qr_type,
            "prediction": "Non-Payment QR",
            "confidence": 100.0,
            "safety_score": 0,
            "risk_level": "Non-Payment",
            "message": "Only payment QR codes are supported.",
            "reason": (
                f"This QR code contains a {qr_type} ('{qr_content[:50]}...'). "
                "CyberGuardian AI exclusively inspects Payment QR codes to protect your financial transactions. "
                "Web links and non-payment codes are NOT accepted or added to your payment history."
            ),
            "recommendation": "Please scan an authentic UPI or merchant payment QR code (PhonePe, Google Pay, Paytm, BHIM, BharatQR).",
            "database_status": "not_saved"
        }

    # 2. Decode QR Image if present
    qr_image = None
    if data.image_data:
        try:
            image_text = data.image_data
            if "," in image_text:
                image_text = image_text.split(",", 1)[1]
            image_bytes = base64.b64decode(image_text)
            image_array = np.frombuffer(image_bytes, dtype=np.uint8)
            qr_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        except Exception as err:
            print("Image decode note:", err)

    # 3. Predict using Stage 2 ML model + payload security verification
    result = predict(qr_image, qr_content)

    prediction = result.get("prediction", "Safe")
    confidence = float(result.get("confidence", 93.0))
    safety_score = int(result.get("safety_score", 95))
    risk_level = result.get("risk_level", "Safe")
    risk_factors = result.get("risk_factors", [])
    recommendation = get_recommendation(risk_level)

    # Compile risk factors text for database storage
    factor_texts = []
    for f in risk_factors:
        if isinstance(f, dict):
            feat = f.get("feature", "")
            imp = f.get("impact", "")
            factor_texts.append(f"{feat}: {imp}")
        else:
            factor_texts.append(str(f))
    risk_factors_str = "; ".join(factor_texts)

    # 4. Save only payment QRs to database
    database_status = "not_saved"
    scan_id = None

    if data.user_id and data.user_id > 0:
        connection = None
        cursor = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO scan_history
                (user_id, qr_content, prediction, confidence, risk_score, risk_level, risk_factors)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                data.user_id,
                qr_content,
                prediction,
                confidence,
                safety_score,
                risk_level,
                risk_factors_str
            ))
            connection.commit()
            scan_id = cursor.lastrowid
            database_status = "saved"
        except Exception as error:
            if connection:
                connection.rollback()
            print("Scan save error:", error)
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    # Returns essential details WITHOUT amount, purpose, or recipient
    return {
        "status": "success",
        "is_payment_qr": True,
        "scan_id": scan_id,
        "prediction": prediction,
        "confidence": confidence,
        "safety_score": safety_score,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "qr_type": qr_type,
        "recommendation": recommendation,
        "database_status": database_status
    }


# ============================================================
# HISTORY ENDPOINTS
# ============================================================

@app.get("/history")
def get_history_query(user_id: int | None = Query(None, ge=1)):
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id query parameter is required.")
    return fetch_user_history(user_id)


@app.get("/history/{user_id}")
def get_history_path(user_id: int):
    return fetch_user_history(user_id)


def fetch_user_history(user_id: int):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, user_id, qr_content, prediction, confidence, risk_score, risk_level, risk_factors, scanned_at
            FROM scan_history
            WHERE user_id = %s
            ORDER BY scanned_at DESC, id DESC
        """, (user_id,))
        history = cursor.fetchall()
        return {"status": "success", "history": history or []}
    except Exception as error:
        print("History fetch error:", error)
        raise HTTPException(status_code=500, detail="Unable to retrieve history.")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.delete("/history/{scan_id}")
def delete_history_item(scan_id: int, user_id: int | None = Query(None)):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()

        if user_id:
            cursor.execute("DELETE FROM scan_history WHERE id = %s AND user_id = %s", (scan_id, user_id))
        else:
            cursor.execute("DELETE FROM scan_history WHERE id = %s", (scan_id,))

        connection.commit()
        return {"status": "success", "message": "History item deleted successfully."}
    except Exception as error:
        if connection:
            connection.rollback()
        print("Delete history error:", error)
        raise HTTPException(status_code=500, detail="Unable to delete history entry.")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.delete("/history")
def clear_user_history(user_id: int = Query(..., ge=1)):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM scan_history WHERE user_id = %s", (user_id,))
        connection.commit()
        return {"status": "success", "message": "Scan history cleared successfully."}
    except Exception as error:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail="Unable to clear history.")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ============================================================
# CHATBOT ENDPOINT
# ============================================================

@app.post("/chat")
def chat(data: ChatData):
    reply = chatbot_reply(data.message, data.scan_context)
    return {
        "status": "success",
        "reply": reply,
        "message": reply
    }
