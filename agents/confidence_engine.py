"""
EmailMind AI Employee
Hybrid Confidence Validation Engine
----------------------------------
This layer decides whether an email can be processed automatically
or requires Human Review.
"""

VALID_INTENTS = [
    "Invoice Submission",
    "Payment Query",
    "Account Access",
    "Dispute",
    "Spam"
]


def validate_classification(primary_intent, detected_intents, confidence):
    """
    Validate Gemini classification.

    Input:
        primary_intent : str | None
        detected_intents : list[str]
        confidence : int

    Returns:
        {
            intent,
            detected_intents,
            confidence,
            review_required,
            status,
            validation_reason
        }
    """

    detected_intents = list(dict.fromkeys(detected_intents))

    # ----------------------------
    # CASE 1 : Multiple Intents
    # ----------------------------
    if len(detected_intents) > 1:
        return {
            "intent": None,
            "detected_intents": detected_intents,
            "confidence": confidence,
            "review_required": True,
            "status": "Pending Review",
            "validation_reason": "Multiple business intents detected."
        }

    # ----------------------------
    # CASE 2 : No Intent Detected
    # ----------------------------
    if primary_intent is None or len(detected_intents) == 0:
        return {
            "intent": None,
            "detected_intents": [],
            "confidence": confidence,
            "review_required": True,
            "status": "Pending Review",
            "validation_reason": "Unable to confidently classify email."
        }

    # ----------------------------
    # CASE 3 : Invalid Intent
    # ----------------------------
    if primary_intent not in VALID_INTENTS:
        return {
            "intent": None,
            "detected_intents": detected_intents,
            "confidence": confidence,
            "review_required": True,
            "status": "Pending Review",
            "validation_reason": "Unknown business intent returned."
        }

    # ----------------------------
    # CASE 4 : Low Confidence
    # ----------------------------
    if confidence < 70:
        return {
            "intent": primary_intent,
            "detected_intents": detected_intents,
            "confidence": confidence,
            "review_required": True,
            "status": "Pending Review",
            "validation_reason": "Confidence below automation threshold."
        }

    # ----------------------------
    # CASE 5 : Medium Confidence
    # ----------------------------
    if 70 <= confidence < 85:
        return {
            "intent": primary_intent,
            "detected_intents": detected_intents,
            "confidence": confidence,
            "review_required": False,
            "status": "Processed",
            "validation_reason": "Medium confidence. Safe to automate."
        }

    # ----------------------------
    # CASE 6 : High Confidence
    # ----------------------------
    return {
        "intent": primary_intent,
        "detected_intents": detected_intents,
        "confidence": confidence,
        "review_required": False,
        "status": "Processed",
        "validation_reason": "High confidence prediction."
    }