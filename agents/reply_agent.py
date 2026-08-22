# ==========================================================
# EmailMind AI Employee - Gemini Draft Reply Agent
# ==========================================================

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-3.5-flash")


def generate_reply(subject, body, intent, action):

    # No reply for spam
    if intent == "Spam":
        return "No draft reply generated because this email was classified as spam."

    # No reply for human review
    if intent == "Human Review":
        return "Draft reply will be generated after human review."

    prompt = f"""
You are EmailMind AI Employee.

Write a professional email reply.

Email Subject:
{subject}

Email Body:
{body}

Detected Intent:
{intent}

Autonomous Action Taken:
{action}

Instructions:
- Thank the sender.
- Mention the request has been processed.
- Mention the action taken.
- Keep it professional.
- Maximum 100 words.
- Return ONLY the email body.
"""

    try:
        response = model.generate_content(prompt)

        if response and response.text:
            return response.text.strip()

        return "AI draft reply could not be generated."

    except Exception as e:
        return f"Gemini Error: {e}"