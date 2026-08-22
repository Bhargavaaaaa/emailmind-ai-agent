import json
import os
from datetime import datetime

TASKS_FILE = "data/tasks.json"

# ---------------------------------------------------------
# CREATE TASK FILE IF NOT EXISTS
# ---------------------------------------------------------

if not os.path.exists(TASKS_FILE):
    with open(TASKS_FILE, "w") as f:
        json.dump([], f)


# ---------------------------------------------------------
# LOAD TASKS SAFELY
# ---------------------------------------------------------

def load_tasks():
    try:
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    except:
        return []


# ---------------------------------------------------------
# SAVE TASKS
# ---------------------------------------------------------

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=4)


# ---------------------------------------------------------
# GENERATE UNIQUE TASK ID
# ---------------------------------------------------------

def generate_task_id():
    return "TASK-" + datetime.now().strftime("%Y%m%d%H%M%S")


# ---------------------------------------------------------
# CREATE AUTONOMOUS TASK
# ---------------------------------------------------------

def create_task(email, team, task_type, priority, description):

    tasks = load_tasks()

    task = {
        "task_id": generate_task_id(),
        "email_id": email["id"],
        "sender": email["sender"],
        "subject": email["subject"],
        "assigned_team": team,
        "task_type": task_type,
        "priority": priority,
        "description": description,
        "status": "Open",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    tasks.append(task)
    save_tasks(tasks)

    return task


# ---------------------------------------------------------
# ACTION ENGINE
# ---------------------------------------------------------

def perform_action(email, validated):
    """
    Executes autonomous business action.

    Returns:
    {
        action,
        team,
        priority,
        task_id
    }
    """

    intent = validated["intent"]

    # ---------------- HUMAN REVIEW ----------------

    if validated["review_required"]:

        task = create_task(
            email=email,
            team="Human Operations",
            task_type="Manual Review",
            priority="High",
            description="Email requires human review because multiple intents or low confidence were detected."
        )

        return {
            "action": "Queued for Human Review",
            "team": task["assigned_team"],
            "priority": task["priority"],
            "task_id": task["task_id"]
        }

    # ---------------- INVOICE ----------------

    if intent == "Invoice Submission":

        task = create_task(
            email=email,
            team="Finance Team",
            task_type="Invoice Processing",
            priority="Medium",
            description="Vendor invoice automatically routed to Finance for processing."
        )

        return {
            "action": "Invoice Processing Task Created",
            "team": task["assigned_team"],
            "priority": task["priority"],
            "task_id": task["task_id"]
        }

    # ---------------- PAYMENT ----------------

    elif intent == "Payment Query":

        task = create_task(
            email=email,
            team="Accounts Payable",
            task_type="Payment Follow-up",
            priority="High",
            description="Vendor payment status request routed to Accounts Payable."
        )

        return {
            "action": "Payment Follow-up Ticket Created",
            "team": task["assigned_team"],
            "priority": task["priority"],
            "task_id": task["task_id"]
        }

    # ---------------- ACCOUNT ACCESS ----------------

    elif intent == "Account Access":

        task = create_task(
            email=email,
            team="IT Helpdesk",
            task_type="Account Access Support",
            priority="High",
            description="Login/account access issue routed to IT Helpdesk."
        )

        return {
            "action": "IT Helpdesk Ticket Created",
            "team": task["assigned_team"],
            "priority": task["priority"],
            "task_id": task["task_id"]
        }

    # ---------------- DISPUTE ----------------

    elif intent == "Dispute":

        task = create_task(
            email=email,
            team="Finance Operations",
            task_type="Invoice Dispute Investigation",
            priority="Critical",
            description="Invoice discrepancy escalated to Finance Operations."
        )

        return {
            "action": "Finance Dispute Investigation Created",
            "team": task["assigned_team"],
            "priority": task["priority"],
            "task_id": task["task_id"]
        }

    # ---------------- SPAM ----------------

    elif intent == "Spam":

        task = create_task(
            email=email,
            team="Security",
            task_type="Spam Detection",
            priority="Low",
            description="Promotional or phishing email marked as spam."
        )

        return {
            "action": "Email Marked as Spam",
            "team": task["assigned_team"],
            "priority": task["priority"],
            "task_id": task["task_id"]
        }

    # ---------------- UNKNOWN ----------------

    task = create_task(
        email=email,
        team="Human Operations",
        task_type="Unknown Email",
        priority="Medium",
        description="Unknown business email routed for manual verification."
    )

    return {
        "action": "Queued for Human Review",
        "team": task["assigned_team"],
        "priority": task["priority"],
        "task_id": task["task_id"]
    }


# ---------------------------------------------------------
# HUMAN RESOLVES TASK
# ---------------------------------------------------------

def resolve_task(task_id):

    tasks = load_tasks()

    for task in tasks:
        if task["task_id"] == task_id:
            task["status"] = "Resolved"
            task["resolved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    save_tasks(tasks)


# ---------------------------------------------------------
# FETCH OPEN TASKS
# ---------------------------------------------------------

def fetch_open_tasks():
    tasks = load_tasks()
    return [t for t in tasks if t["status"] == "Open"]


# ---------------------------------------------------------
# FETCH ALL TASKS
# ---------------------------------------------------------

def fetch_all_tasks():
    return load_tasks()