import re

CHAT_KNOWLEDGE = {
    "greetings": [
        "Hello! I am your CyberGuardian AI security assistant. Ask me about your scanned QR code, UPI payment safety, or how to avoid financial scams.",
        "Hi there! How can I help protect your payments today? You can ask about your recent scan or general payment security.",
        "Hey! I'm here to help ensure your QR and UPI payments are safe. What questions do you have?"
    ],
    "pin": (
        "🔒 Critical Rule: NEVER enter your UPI PIN to receive money or get a refund. "
        "A UPI PIN is ONLY entered when money is leaving your account to authorize an outgoing payment. "
        "Anyone who asks for your UPI PIN or asks you to enter it to 'receive' money is attempting a scam."
    ),
    "otp": (
        "🛡️ Never share your One-Time Password (OTP) with anyone, not even bank representatives. "
        "Legitimate banks and payment apps never ask for your OTP over phone, SMS, or chat."
    ),
    "refund": (
        "⚠️ Beware of Refund Scams: In genuine UPI transactions, refunds are credited directly to your bank account automatically. "
        "A real refund NEVER requires you to scan a QR code, open a link, or enter your UPI PIN. If someone asks you to do so, decline immediately."
    ),
    "reward": (
        "🎁 Beware of Reward / Cashback Scams: Fraudsters frequently generate QR codes claiming 'Scan to claim ₹2,000 cashback' or 'Win lottery reward'. "
        "Scanning these QR codes will initiate a DEBIT transaction from your account, not a credit. Never scan QR codes for unexpected prizes."
    ),
    "upi_safety": (
        "💡 Key UPI Safety Checklist before paying:\n"
        "1. Verify the Payee Name shown on your UPI app matches the merchant/individual.\n"
        "2. Double-check the recipient's UPI ID (handle).\n"
        "3. Confirm the payment amount is exact.\n"
        "4. Beware of paper QR stickers placed on top of official merchant counter QR stands.\n"
        "5. Remember: Entering your UPI PIN always DEBITS your account."
    ),
    "phishing": (
        "🎣 Phishing via QR (Quishing): Attackers generate QR codes that disguise fraudulent payment requests or lead to deceptive cloned websites. "
        "CyberGuardian AI examines the internal QR structure and payment parameters to catch deceptive signs before you approve any transaction."
    ),
    "safety_score": (
        "📊 Safety Score Explained: The Safety Score is a 0 to 100 rating calculated from our trained AI model and payment risk rules.\n"
        "• 80-100: Safe — High confidence, standard payment format.\n"
        "• 50-79: Suspicious / Needs Review — Unverified recipient or unusual instructions.\n"
        "• 0-49: High Risk — Strong indicators of fraudulent intent or deceptive patterns."
    ),
    "confidence": (
        "🎯 AI Confidence: This indicates how firmly the machine learning model supports its prediction. "
        "High confidence (>70%) means the visual and structural features strongly match known patterns."
    ),
    "shap": (
        "🔍 Explainable AI (SHAP): Rather than giving a mysterious 'black box' answer, CyberGuardian uses Explainable AI to show you the exact reasons (like payment parameter validity, QR texture integrity, or deceptive keywords) that drove the safety rating."
    ),
    "qr_type": (
        "💳 Payment QR vs Website QR: CyberGuardian AI exclusively evaluates Payment QR codes (UPI and BharatQR) for financial protection. "
        "Standard website links are not processed as payment scans because this app is focused on keeping your money safe."
    ),
    "help": (
        "🤖 I can assist you with:\n"
        "• Explaining your recent scan results & risk factors\n"
        "• Explaining your Safety Score & AI confidence\n"
        "• Spotting UPI scams (refund, cashback, lottery tricks)\n"
        "• UPI PIN & OTP security best practices\n"
        "• Verifying payment recipients"
    )
}


def get_scan_explanation(scan_context, user_question=""):
    """Generate understandable, human-friendly reasons from the current scan context."""
    if not scan_context:
        return None

    risk = scan_context.get("risk_level", "Unknown")
    score = scan_context.get("safety_score", scan_context.get("risk_score", "N/A"))
    confidence = scan_context.get("confidence")
    factors = scan_context.get("risk_factors", [])
    recipient = scan_context.get("upi_id") or scan_context.get("payee_name") or ""

    factor_descriptions = []
    if isinstance(factors, list):
        for f in factors:
            if isinstance(f, dict):
                feature = f.get("feature", "")
                impact = f.get("impact", "")
                detail = f.get("detail") or f.get("message") or ""
                if detail:
                    factor_descriptions.append(detail)
                elif feature:
                    factor_descriptions.append(f"{feature} ({impact})")
            elif isinstance(f, str) and f.strip():
                factor_descriptions.append(f.strip())

    q = user_question.lower()

    if "score" in q:
        return (
            f"Your current Safety Score is {score}/100 with a risk rating of '{risk}'. "
            f"This score measures structural authenticity and payment security rules."
        )

    if "confidence" in q and confidence is not None:
        return (
            f"The AI model evaluated this QR with {float(confidence):.1f}% confidence. "
            f"This reflects how strongly the pattern matches our trained payment dataset."
        )

    # General reason / why / safe explanation
    reasons_text = ""
    if factor_descriptions:
        reasons_text = " Key observations:\n• " + "\n• ".join(factor_descriptions[:4])

    if risk == "Safe":
        return (
            f"✅ Good news! The current QR code is rated Safe with a Safety Score of {score}/100. "
            f"The payment format is legitimate and no scam indicators were found.{reasons_text}\n"
            f"Tip: Still confirm the recipient ({recipient or 'payee'}) in your UPI app before entering your PIN."
        )
    elif risk in ("Suspicious", "Needs Review"):
        return (
            f"⚠️ Caution: The current scan is rated '{risk}' with a Safety Score of {score}/100.{reasons_text}\n"
            f"Recommendation: Carefully check the payee name and amount. Never proceed if someone requested this payment over phone/chat."
        )
    else:
        return (
            f"🚨 Warning: This QR is rated '{risk}' (Safety Score: {score}/100)!{reasons_text}\n"
            f"Danger: High probability of fraudulent payment or deceptive instructions. Do NOT approve or enter your UPI PIN."
        )


def chatbot_reply(message: str, scan_context: dict = None) -> str:
    text = (message or "").lower().strip()

    if not text:
        return "Please ask a question, and I'll be glad to help!"

    # 1. Check for greetings
    if text in ("hi", "hello", "hey", "greetings", "good morning", "good evening", "namaste"):
        return CHAT_KNOWLEDGE["greetings"][0]

    # 2. Contextual questions regarding the active scan
    if scan_context:
        scan_keywords = ["why", "reason", "explain", "risky", "safe", "score", "confidence", "merchant", "legit", "scan"]
        if any(w in text for w in scan_keywords):
            explanation = get_scan_explanation(scan_context, text)
            if explanation:
                return explanation

    # 3. Specific cybersecurity topics
    if "pin" in text:
        return CHAT_KNOWLEDGE["pin"]

    if "otp" in text:
        return CHAT_KNOWLEDGE["otp"]

    if "refund" in text:
        return CHAT_KNOWLEDGE["refund"]

    if "reward" in text or "cashback" in text or "prize" in text or "lottery" in text:
        return CHAT_KNOWLEDGE["reward"]

    if "receive" in text and ("money" in text or "payment" in text):
        return (
            "⚠️ Remember: You NEVER need to enter your UPI PIN to receive money! "
            "Entering your UPI PIN authorizes money to LEAVE your account. If anyone asks you to enter your PIN to receive funds, it is a scam."
        )

    if "score" in text or "safety score" in text:
        return CHAT_KNOWLEDGE["safety_score"]

    if "confidence" in text:
        return CHAT_KNOWLEDGE["confidence"]

    if "shap" in text or "explainable" in text:
        return CHAT_KNOWLEDGE["shap"]

    if "url" in text or "link" in text or "website" in text:
        return CHAT_KNOWLEDGE["qr_type"]

    if "phishing" in text or "quishing" in text or "fake qr" in text:
        return CHAT_KNOWLEDGE["phishing"]

    if "upi" in text or "how to pay" in text or "checklist" in text:
        return CHAT_KNOWLEDGE["upi_safety"]

    if "help" in text or "what can you do" in text or "features" in text:
        return CHAT_KNOWLEDGE["help"]

    # 4. Fallback with helpful suggestions
    return (
        "I'm here to help with QR security and payment protection! You can ask:\n\n"
        "• 'Why is this QR risky?'\n"
        "• 'Do I need my UPI PIN to receive money?'\n"
        "• 'How do UPI refund scams work?'\n"
        "• 'What does my Safety Score mean?'\n"
        "• 'How can I verify a recipient?'"
    )