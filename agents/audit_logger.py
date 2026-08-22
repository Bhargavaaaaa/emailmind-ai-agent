# ==========================================================
# EmailMind AI Employee - Audit Logger (FINAL V3)
# ==========================================================

import sqlite3
from datetime import datetime
import os

DB_PATH = "emailmind.db"

# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

def initialize_database():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email_id TEXT UNIQUE,
        sender TEXT,
        subject TEXT,
        primary_intent TEXT,
        detected_intents TEXT,
        confidence INTEGER,
        action TEXT,
        assigned_team TEXT,
        priority TEXT,
        status TEXT,
        reason TEXT,
        draft_reply TEXT,
        created_at TEXT,
        resolved_at TEXT,
        resolved_by TEXT
    )
    """)

    conn.commit()
    conn.close()


# Create DB automatically
initialize_database()

# ==========================================================
# SAVE AUDIT LOG
# ==========================================================

def save_audit_log(email, validated, action, reason, draft_reply):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO audit_log (
            email_id,
            sender,
            subject,
            primary_intent,
            detected_intents,
            confidence,
            action,
            assigned_team,
            priority,
            status,
            reason,
            draft_reply,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        email["id"],
        email["sender"],
        email["subject"],
        validated["intent"],
        ",".join(validated["detected_intents"]),
        validated["confidence"],
        action["action"],
        action["team"],
        action["priority"],
        validated["status"],
        reason,
        draft_reply,      # ⭐ THIS SAVES THE GEMINI REPLY
        datetime.now().strftime("%d-%b-%Y %I:%M %p")
    ))

    conn.commit()
    conn.close()

# ==========================================================
# FETCH ALL AUDIT LOGS
# ==========================================================

def fetch_audit_logs():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM audit_log
        ORDER BY id DESC
    """)

    logs = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return logs


# ==========================================================
# FETCH PENDING HUMAN REVIEW EMAILS
# ==========================================================

def fetch_pending_reviews():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM audit_log
        WHERE status='Pending Review'
        ORDER BY id DESC
    """)

    rows = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return rows


# ==========================================================
# RESOLVE HUMAN REVIEW
# ==========================================================

def resolve_review(email_id, selected_intent):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE audit_log
        SET
            primary_intent=?,
            status='Processed',
            resolved_by='Human Operations',
            resolved_at=?
        WHERE email_id=?
    """, (
        selected_intent,
        datetime.now().strftime("%d-%b-%Y %I:%M %p"),
        email_id
    ))

    conn.commit()
    conn.close()


# ==========================================================
# DASHBOARD METRICS
# ==========================================================

def get_dashboard_metrics():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM audit_log")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM audit_log WHERE status='Processed'")
    processed = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM audit_log WHERE status='Pending Review'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM audit_log WHERE primary_intent='Spam'")
    spam = cursor.fetchone()[0]

    conn.close()

    return {
        "total": total,
        "processed": processed,
        "pending": pending,
        "spam": spam
    }


# ==========================================================
# EMAILS PROCESSED TODAY
# ==========================================================

def emails_today():

    today = datetime.now().strftime("%d-%b-%Y")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM audit_log
        WHERE created_at LIKE ?
    """, (today + "%",))

    count = cursor.fetchone()[0]

    conn.close()

    return count


# ==========================================================
# CATEGORY DISTRIBUTION
# ==========================================================

def category_distribution_today():

    today = datetime.now().strftime("%d-%b-%Y")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT primary_intent, COUNT(*)
        FROM audit_log
        WHERE created_at LIKE ?
        GROUP BY primary_intent
    """, (today + "%",))

    rows = cursor.fetchall()

    conn.close()

    return rows


# ==========================================================
# ACTION DISTRIBUTION
# ==========================================================

def action_distribution_today():

    today = datetime.now().strftime("%d-%b-%Y")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT action, COUNT(*)
        FROM audit_log
        WHERE created_at LIKE ?
        GROUP BY action
    """, (today + "%",))

    rows = cursor.fetchall()

    conn.close()

    return rows


# ==========================================================
# HOURLY TREND
# ==========================================================

def hourly_processing_trend():

    today = datetime.now().strftime("%d-%b-%Y")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT SUBSTR(created_at,13,2) AS hour,
               COUNT(*)
        FROM audit_log
        WHERE created_at LIKE ?
        GROUP BY hour
        ORDER BY hour
    """, (today + "%",))

    rows = cursor.fetchall()

    conn.close()

    return rows


# ==========================================================
# CONFIDENCE TREND
# ==========================================================

def confidence_trend_today():

    today = datetime.now().strftime("%d-%b-%Y")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT SUBSTR(created_at,13,2) AS hour,
               AVG(confidence)
        FROM audit_log
        WHERE created_at LIKE ?
        GROUP BY hour
        ORDER BY hour
    """, (today + "%",))

    rows = cursor.fetchall()

    conn.close()

    return rows


# ==========================================================
# LAST 7 DAYS SUMMARY
# ==========================================================

def last_seven_days_summary():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            SUBSTR(created_at,1,11) AS day,
            COUNT(*) AS emails,
            SUM(CASE WHEN status='Processed' THEN 1 ELSE 0 END) AS processed,
            SUM(CASE WHEN status='Pending Review' THEN 1 ELSE 0 END) AS pending
        FROM audit_log
        GROUP BY day
        ORDER BY id DESC
        LIMIT 7
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows