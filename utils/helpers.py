import json

def load_emails():
    with open("data/emails.json", "r") as file:
        return json.load(file)