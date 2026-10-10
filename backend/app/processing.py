"""Background processing: turns PENDING certificate rows into PDFs.

Flow: validate recipient -> render PDF -> mark DONE.
Every certificate has its own try/except, so one failure never stops the rest.
"""
import os
from concurrent.futures import ThreadPoolExecutor

from . import certificate_renderer
from .models import STATUS_DONE, STATUS_FAILED, STATUS_PENDING, Certificate, Job, db
from .validation import validate_recipient

# Two workers: enough to run jobs side by side, few enough that SQLite
# (one writer at a time) is not overloaded.
executor = ThreadPoolExecutor(max_workers=2)


def start_processing(app, job_id):
    """Hand the job to the background pool and return immediately.

    When SYNC_PROCESSING is on (tests only) the job runs inline instead,
    which makes tests deterministic. Never turn it on for real use.
    """
    if app.config["SYNC_PROCESSING"]:
        process_job(app, job_id)
    else:
        executor.submit(process_job, app, job_id)


def process_job(app, job_id):
    # A worker thread has no request, so it must open its own app context.
    # That gives it its OWN database session. The request's session is closed
    # once the response is sent and is not safe to share across threads.
    with app.app_context():
        try:
            run_job(job_id)
        except Exception:
            app.logger.exception("Job %s crashed unexpectedly", job_id)
        finally:
            db.session.remove()


def run_job(job_id):
    pending_rows = (
        Certificate.query.filter_by(job_id=job_id, status=STATUS_PENDING)
        .order_by(Certificate.id)
        .all()
    )
    # Keep only the ids: after a rollback the row objects are expired,
    # so each certificate is re-loaded fresh by id.
    certificate_ids = []
    for row in pending_rows:
        certificate_ids.append(row.id)

    for certificate_id in certificate_ids:
        process_one(certificate_id)


def process_one(certificate_id):
    try:
        generate_certificate(certificate_id)
    except Exception as exc:
        db.session.rollback()
        message = f"Certificate generation failed: {exc.__class__.__name__}: {exc}"
        mark_failed(certificate_id, message)


def generate_certificate(certificate_id):
    cert = db.session.get(Certificate, certificate_id)
    job = db.session.get(Job, cert.job_id)

    problem = validate_recipient(cert.recipient_name, cert.recipient_email)
    if problem is not None:
        cert.status = STATUS_FAILED
        cert.error_message = problem
        db.session.commit()
        return

    output_path = pdf_path(job.id, cert.id)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    certificate_renderer.render_certificate(
        output_path=output_path,
        recipient_name=cert.recipient_name,
        event_name=job.event_name,
        issue_date=job.issue_date,
        issuer_name=job.issuer_name,
        verify_url=verify_url(cert.verification_token),
    )

    cert.file_path = output_path
    cert.status = STATUS_DONE
    cert.error_message = None
    db.session.commit()


def mark_failed(certificate_id, message):
    cert = db.session.get(Certificate, certificate_id)
    cert.status = STATUS_FAILED
    cert.error_message = message
    db.session.commit()


def pdf_path(job_id, certificate_id):
    # Named by id, never by recipient name: names can collide ("Rahul Kumar"
    # twice) and user text inside a file path is a path-injection risk.
    from flask import current_app

    folder = os.path.join(current_app.config["STORAGE_DIR"], f"{job_id}")
    return os.path.join(folder, f"{certificate_id}.pdf")


def verify_url(token):
    from flask import current_app

    return f"{current_app.config['BASE_URL']}/verify/{token}"
