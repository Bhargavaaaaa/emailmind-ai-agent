# ==========================================================
# EmailMind AI Employee
# Part 1/6
# ==========================================================

import streamlit as st
import pandas as pd
import time

from streamlit_autorefresh import st_autorefresh

from agents.gmail_reader import (
    get_unread_emails,
    mark_as_processed
)

from agents.classifier import classify_email
from agents.confidence_engine import validate_classification
from agents.action_engine import perform_action
from agents.reply_agent import generate_reply

from agents.audit_logger import (
    initialize_database,
    save_audit_log,
    fetch_audit_logs,
    fetch_pending_reviews,
    resolve_review,
    get_dashboard_metrics,
    emails_today
)

# ---------------- Page Config ----------------

st.set_page_config(
    page_title="EmailMind AI Employee",
    page_icon="🤖",
    layout="wide"
)

initialize_database()

# ---------------- Auto Refresh ----------------
# Checks Gmail every 15 seconds

st_autorefresh(interval=15000, key="gmail_refresh")

# ---------------- Session State ----------------

if "processed_emails" not in st.session_state:
    st.session_state.processed_emails = []

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.strftime("%I:%M:%S %p")

# ---------------- Sidebar ----------------

st.sidebar.title("🤖 EmailMind AI Employee")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "📨 Inbox Processing",
        "👤 Human Review Queue",
        "📋 Audit Trail"
    ]
)

st.sidebar.divider()

st.sidebar.success("🟢 Gmail Connected")
st.sidebar.success("🟢 Gemini AI Active")

st.sidebar.caption(
    f"Last Sync : {st.session_state.last_refresh}"
)
# ==========================================================
# PART 2/6 — Process New Gmail Emails
# ==========================================================

def process_new_emails():
    """
    Reads unread Gmail emails, classifies them using Gemini,
    takes autonomous action, generates AI draft reply,
    stores everything in Audit Trail, and marks Gmail as read.
    """

    emails = get_unread_emails()

    if not emails:
        return []

    processed = []

    for email in emails:

        # ---------------- AI Classification ----------------
        ai_result = classify_email(
            email["subject"],
            email["body"]
        )

        # ---------------- Confidence Validation ----------------
        validated = validate_classification(
            ai_result["primary_intent"],
            ai_result["detected_intents"],
            ai_result["confidence"]
        )

        # ---------------- Autonomous Action ----------------
        action = perform_action(email, validated)

        # ---------------- Gemini AI Draft Reply ----------------
        draft_reply = generate_reply(
            subject=email["subject"],
            body=email["body"],
            intent=validated["intent"],
            action=action["action"]
        )

        # ---------------- Save to Audit Trail ----------------
        save_audit_log(
            email=email,
            validated=validated,
            action=action,
            reason=ai_result["reason"],
            draft_reply=draft_reply
        )

        # ---------------- Mark Email as Processed in Gmail ----------------
        mark_as_processed(email["id"])

        # ---------------- Keep Only Live Inbox Emails ----------------
        processed.append({
            "email_id": email["id"],
            "sender": email["sender"],
            "subject": email["subject"],
            "body": email["body"],

            "primary_intent": validated["intent"],
            "detected_intents": validated["detected_intents"],
            "confidence": validated["confidence"],

            "status": validated["status"],
            "action": action["action"],
            "assigned_team": action["team"],
            "priority": action["priority"],
            "task_id": action["task_id"],

            "reason": ai_result["reason"],

            # Saved only for Audit Trail
            "draft_reply": draft_reply
        })

    st.session_state.last_refresh = time.strftime("%I:%M:%S %p")

    return processed


# ==========================================================
# Auto Process New Emails Every Refresh
# ==========================================================

# ==========================================================
# Auto Process New Emails Every Refresh (FIXED)
# ==========================================================

# Initialize session values only once
if "processed_emails" not in st.session_state:
    st.session_state.processed_emails = []

if "last_email" not in st.session_state:
    st.session_state.last_email = None

# Check Gmail for new unread emails
new_emails = process_new_emails()

if new_emails:
    # Add new emails to current session history
    st.session_state.processed_emails.extend(new_emails)

    # Keep only the newest email for Inbox Processing
    st.session_state.last_email = new_emails[-1]

    st.session_state.last_refresh = time.strftime("%I:%M:%S %p")

# IMPORTANT: Do NOT clear processed_emails or last_email.

# ==========================================================
# PART 3/6 — Dashboard
# ==========================================================
if page == "🏠 Dashboard":

    st.title("🤖 EmailMind AI Employee")
    st.caption("Autonomous Email-to-Action Agent")

    metrics = get_dashboard_metrics()

    # KPI Cards
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("📨 Total Emails", metrics["total"])
    c2.metric("✅ Auto Processed", metrics["processed"])
    c3.metric("🟡 Pending Review", metrics["pending"])
    c4.metric("🚫 Spam Blocked", metrics["spam"])

    st.divider()

    # Today's Summary (Only 3 Metrics)
    st.subheader("📅 Today's Summary")

    success_rate = 0
    if metrics["total"] > 0:
        success_rate = round((metrics["processed"] / metrics["total"]) * 100)

    logs = fetch_audit_logs()

    avg_confidence = 0
    if logs:
        values = [log["confidence"] for log in logs if log["confidence"]]
        if values:
            avg_confidence = round(sum(values) / len(values))

    col1, col2, col3 = st.columns(3)

    col1.metric("Today's Emails", emails_today())
    col2.metric("Automation Success", f"{success_rate}%")
    col3.metric("Average AI Confidence", f"{avg_confidence}%")
    
# ==========================================================
# PART 4/6 — Inbox Processing (Live Emails Only)
# ==========================================================
# ==========================================================
# PART 4/6 — Inbox Processing (FINAL VERSION)
# ==========================================================

elif page == "📨 Inbox Processing":

    st.title("📨 Inbox Processing")
    st.caption("Shows the most recently analyzed email. The next new email will replace it.")

    # Get the latest analyzed email
    latest_email = st.session_state.get("last_email", None)

    if latest_email is None:
        st.success("🎉 Inbox is clear. No emails have been analyzed yet.")
        st.caption("EmailMind AI Employee is monitoring Gmail for new unread emails.")

    else:

        st.info("📬 Last Email Analyzed by AI")

        with st.container(border=True):

            # ---------------- Header ----------------

            left, right = st.columns([5, 1])

            with left:
                st.markdown(f"### {latest_email['subject']}")
                st.caption(f"📧 {latest_email['sender']}")

            with right:
                if latest_email["status"] == "Processed":
                    st.success("Processed")
                else:
                    st.warning("Pending Review")

            st.divider()

            # ---------------- Email Details ----------------

            c1, c2, c3 = st.columns(3)

            with c1:
                st.markdown("**Category**")
                st.info(latest_email["primary_intent"])

            with c2:
                st.markdown("**Confidence**")
                st.success(f"{latest_email['confidence']}%")

            with c3:
                st.markdown("**Priority**")
                st.warning(latest_email["priority"])

            st.write("**Assigned Team**")
            st.write(latest_email["assigned_team"])

            st.write("**Autonomous Action Taken**")
            st.success(latest_email["action"])

            # Multiple intents (if ambiguous)
            if len(latest_email["detected_intents"]) > 1:
                st.write("**Detected Multiple Intents**")
                st.write(", ".join(latest_email["detected_intents"]))

            st.write("**AI Reasoning**")
            st.info(latest_email["reason"])

            st.divider()

            st.success("✅ This email has been processed and stored permanently in the Audit Trail.")

# ==========================================================
# PART 5/6 — Human Review Queue
# ==========================================================

elif page == "👤 Human Review Queue":

    st.title("👤 Human Review Queue")
    st.caption("Only ambiguous or low-confidence emails appear here for manual review.")

    pending_reviews = fetch_pending_reviews()

    if not pending_reviews:
        st.success("🎉 No emails are waiting for human review.")

    else:
        st.warning(f"{len(pending_reviews)} email(s) require human review.")

        for email in pending_reviews:

            with st.container(border=True):

                left, right = st.columns([5, 1])

                with left:
                    st.markdown(f"### {email['subject']}")
                    st.caption(f"📧 {email['sender']}")

                with right:
                    st.warning("Pending Review")

                st.write("**Detected Intents**")
                st.info(email["detected_intents"])

                st.write("**AI Confidence**")
                st.warning(f"{email['confidence']}%")

                st.write("**Why Human Review?**")
                st.caption(email["reason"])

                st.divider()

                selected_intent = st.selectbox(
                    "Select Final Category",
                    [
                        "Invoice Submission",
                        "Payment Query",
                        "Dispute",
                        "Account Access",
                        "Spam"
                    ],
                    key=f"intent_{email['email_id']}"
                )

                if st.button("✅ Resolve Email", key=f"resolve_{email['email_id']}"):

                    resolve_review(
                        email["email_id"],
                        selected_intent
                    )

                    st.success(
                        f"Email resolved as '{selected_intent}' and moved to Audit Trail."
                    )

                    st.rerun()

# ==========================================================
# PART 6/6 — Audit Trail (Permanent History)
# ==========================================================

elif page == "📋 Audit Trail":

    st.title("📋 Audit Trail")
    st.caption("Permanent history of every AI decision and autonomous action.")

    logs = fetch_audit_logs()

    if not logs:
        st.info("No audit records available.")

    else:

        df = pd.DataFrame(logs)

        # ---------------- Filters ----------------

        col1, col2 = st.columns(2)

        with col1:
            category = st.selectbox(
                "Category",
                ["All"] + sorted(df["primary_intent"].dropna().unique().tolist())
            )

        with col2:
            status = st.selectbox(
                "Status",
                ["All"] + sorted(df["status"].dropna().unique().tolist())
            )

        if category != "All":
            df = df[df["primary_intent"] == category]

        if status != "All":
            df = df[df["status"] == status]

        st.divider()

        # ---------------- Audit Table ----------------

        st.subheader("Email Processing History")

        headers = st.columns([1.2, 1.5, 2.5, 1.5, 2.2, 1])

        headers[0].markdown("**Time**")
        headers[1].markdown("**Category**")
        headers[2].markdown("**Subject**")
        headers[3].markdown("**Status**")
        headers[4].markdown("**Action**")
        headers[5].markdown("**Reply**")

        st.markdown("---")

        for index, row in df.iterrows():

            cols = st.columns([1.2, 1.5, 2.5, 1.5, 2.2, 1])

            cols[0].caption(row["created_at"])
            cols[1].write(row["primary_intent"])
            cols[2].write(row["subject"])
            cols[3].write(row["status"])
            cols[4].write(row["action"])

            with cols[5]:
                with st.popover("View"):
                    st.markdown("### ✉️ AI Draft Reply")

                    st.write(row["draft_reply"])

                    st.markdown("---")

                    st.markdown("**AI Reasoning**")
                    st.caption(row["reason"])

                    st.markdown("**Assigned Team**")
                    st.write(row["assigned_team"])

                    st.markdown("**Confidence**")
                    st.write(f"{row['confidence']}%")

            st.markdown("---")

        # ---------------- Download CSV ----------------

        st.download_button(
            "📥 Download Audit Trail CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name="emailmind_audit_trail.csv",
            mime="text/csv",
            use_container_width=True
        )