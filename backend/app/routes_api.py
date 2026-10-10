import io
import os
import zipfile

from flask import Blueprint, current_app, jsonify, request, send_file

from . import services
from .models import STATUS_DONE, Certificate, Job, db
from .processing import start_processing
from .validation import validate_request

api = Blueprint("api", __name__)


def error_response(message, status_code, details=None):
    body = {"error": message}
    if details is not None:
        body["details"] = details
    return jsonify(body), status_code


@api.route("/health")
def health():
    return jsonify(status="ok")


@api.route("/api/jobs", methods=["POST"])
def create_job():
    data = request.get_json(silent=True)  # None if the body is not valid JSON
    errors = validate_request(data)
    if len(errors) > 0:
        return error_response("Invalid request", 400, errors)

    job = services.create_job(data)
    job_id = job.id
    summary = services.job_summary(job)

    # _get_current_object() gives the real app, which the worker thread needs.
    start_processing(current_app._get_current_object(), job_id)

    return jsonify(job_id=job_id, status=summary["status"], total=summary["total"]), 202


@api.route("/api/jobs")
def list_jobs():
    return jsonify(services.recent_jobs())


@api.route("/api/jobs/<int:job_id>")
def get_job(job_id):
    job = db.session.get(Job, job_id)
    if job is None:
        return error_response("Job not found", 404)
    result = services.job_summary(job)
    result["failures"] = services.job_failures(job_id)
    return jsonify(result)


@api.route("/api/jobs/<int:job_id>/certificates")
def get_job_certificates(job_id):
    job = db.session.get(Job, job_id)
    if job is None:
        return error_response("Job not found", 404)
    return jsonify(services.list_certificates(job_id))


@api.route("/api/certificates/<int:certificate_id>/download")
def download_certificate(certificate_id):
    cert = db.session.get(Certificate, certificate_id)
    if cert is None or cert.status != STATUS_DONE:
        return error_response("Certificate is not available", 404)
    if cert.file_path is None or not os.path.exists(cert.file_path):
        return error_response("Certificate file is missing on the server", 404)
    return send_file(
        cert.file_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"certificate_{cert.id}.pdf",  # never user-supplied text
    )


@api.route("/api/jobs/<int:job_id>/download")
def download_job_zip(job_id):
    job = db.session.get(Job, job_id)
    if job is None:
        return error_response("Job not found", 404)

    done_rows = (
        Certificate.query.filter_by(job_id=job_id, status=STATUS_DONE)
        .order_by(Certificate.id)
        .all()
    )
    buffer = io.BytesIO()
    files_added = 0
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for cert in done_rows:
            if cert.file_path is not None and os.path.exists(cert.file_path):
                archive.write(cert.file_path, arcname=f"certificate_{cert.id}.pdf")
                files_added = files_added + 1

    if files_added == 0:
        return error_response("No completed certificates yet", 404)

    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"job_{job_id}_certificates.zip",
    )


@api.route("/api/verify/<token>")
def verify(token):
    cert = Certificate.query.filter_by(verification_token=token).first()
    if cert is None or cert.status != STATUS_DONE:
        return jsonify(valid=False), 404
    job = db.session.get(Job, cert.job_id)
    return jsonify(
        valid=True,
        recipient_name=cert.recipient_name,
        event_name=job.event_name,
        issue_date=job.issue_date,
        issuer_name=job.issuer_name,
    )
