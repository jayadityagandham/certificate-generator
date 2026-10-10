import uuid
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Certificate statuses. A job's status is NOT stored; it is derived from these.
STATUS_PENDING = "PENDING"
STATUS_DONE = "DONE"
STATUS_FAILED = "FAILED"


def utc_now():
    # Stored as naive UTC because SQLite does not keep timezone information.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def new_token():
    # Random, unguessable id used in the QR code verification link.
    return uuid.uuid4().hex


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.Text, nullable=False)
    issue_date = db.Column(db.Text, nullable=False)
    issuer_name = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)


class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False, index=True)
    recipient_name = db.Column(db.Text, nullable=False, default="")
    recipient_email = db.Column(db.Text, nullable=False, default="")
    status = db.Column(db.String(10), nullable=False, default=STATUS_PENDING, index=True)
    error_message = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.Text, nullable=True)
    verification_token = db.Column(
        db.String(32), nullable=False, unique=True, index=True, default=new_token
    )
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
