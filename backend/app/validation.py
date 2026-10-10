import re
from datetime import datetime

MAX_RECIPIENTS = 1000
MAX_NAME_LENGTH = 100
MAX_EMAIL_LENGTH = 254
MAX_TEXT_LENGTH = 200

DATE_SHAPE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EMAIL_SHAPE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_request(data):
    """Layer 1: is the whole request sane? Returns a list of error messages.

    Individual recipients are NOT checked here, so one bad recipient never
    causes the whole request to be rejected.
    """
    if not isinstance(data, dict):
        return ["Request body must be a JSON object"]

    errors = []

    for field in ("event_name", "issuer_name"):
        value = data.get(field)
        if not isinstance(value, str) or value.strip() == "":
            errors.append(field + " is required")
        elif len(value.strip()) > MAX_TEXT_LENGTH:
            errors.append(field + " must be at most 200 characters")

    errors.extend(check_issue_date(data.get("issue_date")))
    errors.extend(check_recipients_list(data.get("recipients")))
    return errors


def check_issue_date(value):
    message = "issue_date must be a valid date in YYYY-MM-DD format"
    if not isinstance(value, str):
        return ["issue_date is required (YYYY-MM-DD)"]
    value = value.strip()
    if not DATE_SHAPE.match(value):
        return [message]
    try:
        # The pattern only checks the shape; strptime rejects 2026-02-30.
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return [message]
    return []


def check_recipients_list(value):
    if not isinstance(value, list):
        return ["recipients must be a list"]
    if len(value) == 0:
        return ["recipients must not be empty"]
    if len(value) > MAX_RECIPIENTS:
        return [f"recipients must contain at most {MAX_RECIPIENTS} entries (got {len(value)})"]
    return []


def validate_recipient(name, email):
    """Layer 2: is this one recipient valid? Returns an error message or None.

    Called inside the processing loop. A problem here fails only this one
    certificate; the rest of the job carries on.
    """
    name = name.strip()
    email = email.strip()

    if name == "":
        return "name is required"
    if len(name) > MAX_NAME_LENGTH:
        return f"name is too long ({len(name)} characters, maximum {MAX_NAME_LENGTH})"
    if email == "":
        return "email is required"
    if len(email) > MAX_EMAIL_LENGTH:
        return f"email is too long (maximum {MAX_EMAIL_LENGTH} characters)"
    if not EMAIL_SHAPE.match(email):
        return f"email '{email}' is not a valid email address"
    return None
