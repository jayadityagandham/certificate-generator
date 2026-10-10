"""Shared logic used by the API routes: creating jobs and summarising them."""
from sqlalchemy import func

from .models import (
    STATUS_DONE,
    STATUS_FAILED,
    STATUS_PENDING,
    Certificate,
    Job,
    db,
)


def text_or_empty(value):
    # Recipient data arrives as loose JSON. Anything that is not text
    # (null, a number, a list) becomes "", and then fails validation later
    # with a clear message instead of crashing the request.
    if isinstance(value, str):
        return value
    return ""


def build_certificate(job_id, entry):
    if not isinstance(entry, dict):
        # There is nothing to read from this entry, so it fails straight away.
        return Certificate(
            job_id=job_id,
            status=STATUS_FAILED,
            error_message="recipient entry is not an object",
        )
    return Certificate(
        job_id=job_id,
        recipient_name=text_or_empty(entry.get("name")),
        recipient_email=text_or_empty(entry.get("email")),
        status=STATUS_PENDING,
    )


def create_job(data):
    """Create the job and ALL its certificate rows in one go.

    Rows start as PENDING, so progress is simply "count rows by status".
    The request must already have passed validate_request().
    """
    job = Job(
        event_name=data["event_name"].strip(),
        issue_date=data["issue_date"].strip(),
        issuer_name=data["issuer_name"].strip(),
    )
    db.session.add(job)
    db.session.flush()  # assigns job.id without committing yet

    for entry in data["recipients"]:
        db.session.add(build_certificate(job.id, entry))

    db.session.commit()
    return job


def count_by_status(job_id):
    counts = {STATUS_PENDING: 0, STATUS_DONE: 0, STATUS_FAILED: 0}
    rows = (
        db.session.query(Certificate.status, func.count(Certificate.id))
        .filter(Certificate.job_id == job_id)
        .group_by(Certificate.status)
        .all()
    )
    for status, number in rows:
        counts[status] = number
    return counts


def derive_status(pending, failed):
    # The job status is never stored, so it can never disagree with its rows.
    if pending > 0:
        return "PROCESSING"
    if failed > 0:
        return "COMPLETED_WITH_ERRORS"
    return "COMPLETED"


def job_summary(job):
    counts = count_by_status(job.id)
    pending = counts[STATUS_PENDING]
    done = counts[STATUS_DONE]
    failed = counts[STATUS_FAILED]
    return {
        "job_id": job.id,
        "event_name": job.event_name,
        "issue_date": job.issue_date,
        "issuer_name": job.issuer_name,
        "status": derive_status(pending, failed),
        "total": pending + done + failed,
        "pending": pending,
        "done": done,
        "failed": failed,
        "created_at": job.created_at.isoformat() + "Z",
    }


def job_failures(job_id):
    failures = []
    rows = (
        Certificate.query.filter_by(job_id=job_id, status=STATUS_FAILED)
        .order_by(Certificate.id)
        .all()
    )
    for cert in rows:
        failures.append(
            {
                "certificate_id": cert.id,
                "recipient_name": cert.recipient_name,
                "error": cert.error_message,
            }
        )
    return failures


def list_certificates(job_id):
    result = []
    rows = Certificate.query.filter_by(job_id=job_id).order_by(Certificate.id).all()
    for cert in rows:
        result.append(
            {
                "id": cert.id,
                "recipient_name": cert.recipient_name,
                "recipient_email": cert.recipient_email,
                "status": cert.status,
                "error": cert.error_message,
                "verification_token": cert.verification_token,
            }
        )
    return result


def recent_jobs(limit=50):
    result = []
    for job in Job.query.order_by(Job.id.desc()).limit(limit).all():
        result.append(job_summary(job))
    return result
