import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

# -------------------------------------------------------
# LOAD GEMINI API
# -------------------------------------------------------

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3.5-flash")
else:
    model = None


# -------------------------------------------------------
# VALID BUSINESS CATEGORIES
# -------------------------------------------------------

VALID_INTENTS = [
    "Invoice Submission",
    "Payment Query",
    "Account Access",
    "Dispute",
    "Spam"
]


# -------------------------------------------------------
# GEMINI PROMPT
# -------------------------------------------------------

SYSTEM_PROMPT = """
You are EmailMind AI Employee.

Classify a business email.

Choose ONLY these business intents:

1. Invoice Submission
2. Payment Query
3. Account Access
4. Dispute
5. Spam

IMPORTANT RULES

- If email clearly belongs to ONE category:
    detected_intents should contain one item.

- If email contains MULTIPLE business intents
  (example Payment + Dispute),
  detected_intents should contain multiple items.

- Do NOT invent categories.

Return ONLY JSON.

Example:

{
 "primary_intent":"Payment Query",
 "detected_intents":["Payment Query"],
 "confidence":94,
 "reason":"Vendor requested payment status."
}

Ambiguous Example:

{
 "primary_intent": null,
 "detected_intents":["Payment Query","Dispute"],
 "confidence":68,
 "reason":"Email asks payment status and reports invoice mismatch."
}
"""


# -------------------------------------------------------
# LOCAL HYBRID FALLBACK
# -------------------------------------------------------

def local_classifier(email_text):

    text = email_text.lower()

    intents = []

    invoice_keywords = [
        "invoice",
        "attached invoice",
        "billing document",
        "invoice attached",
        "tax invoice"
    ]

    payment_keywords = [
        "payment",
        "settlement",
        "paid",
        "refund",
        "transaction",
        "outstanding payment",
        "pending payment"
    ]

    access_keywords = [
        "login",
        "password",
        "account locked",
        "otp",
        "access",
        "cannot login",
        "unable to login"
    ]

    dispute_keywords = [
        "gst",
        "incorrect amount",
        "mismatch",
        "wrong invoice",
        "quantity mismatch",
        "purchase order",
        "difference"
    ]

    spam_keywords = [
        "reward",
        "winner",
        "lottery",
        "claim now",
        "click here",
        "free iphone",
        "offer expires"
    ]

    if any(word in text for word in invoice_keywords):
        intents.append("Invoice Submission")

    if any(word in text for word in payment_keywords):
        intents.append("Payment Query")

    if any(word in text for word in access_keywords):
        intents.append("Account Access")

    if any(word in text for word in dispute_keywords):
        intents.append("Dispute")

    if any(word in text for word in spam_keywords):
        intents.append("Spam")

    intents = list(dict.fromkeys(intents))

    # Multiple intents
    if len(intents) > 1:
        return {
            "primary_intent": None,
            "detected_intents": intents,
            "confidence": 68,
            "reason": "Multiple business intents detected."
        }

    # Single intent
    if len(intents) == 1:
        return {
            "primary_intent": intents[0],
            "detected_intents": intents,
            "confidence": 88,
            "reason": "Detected using local hybrid classifier."
        }

    # Unknown
    return {
        "primary_intent": None,
        "detected_intents": [],
        "confidence": 50,
        "reason": "Unable to confidently classify email."
    }


# -------------------------------------------------------
# MAIN CLASSIFIER
# -------------------------------------------------------

def classify_email(subject, body):

    email_text = f"""
Subject:
{subject}

Body:
{body}
"""

    # ---------------- GEMINI ----------------

    if model:

        try:

            response = model.generate_content(
                SYSTEM_PROMPT + "\n\nEMAIL:\n" + email_text
            )

            text = response.text.strip()
            text = text.replace("```json", "")
            text = text.replace("```", "").strip()

            result = json.loads(text)

            # Safety Checks
            primary = result.get("primary_intent")
            detected = result.get("detected_intents", [])

            if primary is not None and primary not in VALID_INTENTS:
                return local_classifier(email_text)

            detected = [i for i in detected if i in VALID_INTENTS]

            result["detected_intents"] = detected
            result["primary_intent"] = primary
            result["confidence"] = int(result.get("confidence", 70))

            return result

        except Exception as e:

            fallback = local_classifier(email_text)
            fallback["reason"] = f"Gemini fallback used ({str(e)})"

            return fallback

    # ---------------- NO GEMINI ----------------

    return local_classifier(email_text)