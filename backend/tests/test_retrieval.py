import io
import zipfile

from app import services

from conftest import GOOD_RECIPIENTS


def certificates_of(client, job_id):
    return client.get(f"/api/jobs/{job_id}/certificates").get_json()


def test_certificate_list_shows_each_recipient(client, submit_job):
    job_id = submit_job(GOOD_RECIPIENTS + [{"name": "", "email": "x@example.com"}]).get_json()["job_id"]
    rows = certificates_of(client, job_id)

    assert len(rows) == 3
    assert rows[0]["status"] == "DONE"
    assert rows[2]["status"] == "FAILED"
    assert rows[2]["error"] == "name is required"


def test_single_certificate_downloads_as_pdf(client, submit_job):
    job_id = submit_job(GOOD_RECIPIENTS).get_json()["job_id"]
    cert_id = certificates_of(client, job_id)[0]["id"]

    response = client.get(f"/api/certificates/{cert_id}/download")

    assert response.status_code == 200
    assert response.content_type == "application/pdf"
    assert response.data.startswith(b"%PDF")
    assert f"certificate_{cert_id}.pdf" in response.headers["Content-Disposition"]


def test_failed_certificate_has_no_download(client, submit_job):
    job_id = submit_job([{"name": "", "email": "x@example.com"}]).get_json()["job_id"]
    cert_id = certificates_of(client, job_id)[0]["id"]

    assert client.get(f"/api/certificates/{cert_id}/download").status_code == 404


def test_pending_certificate_has_no_download(app, client, make_payload):
    with app.app_context():
        job = services.create_job(make_payload(GOOD_RECIPIENTS))  # not processed
        job_id = job.id
    cert_id = certificates_of(client, job_id)[0]["id"]

    assert client.get(f"/api/certificates/{cert_id}/download").status_code == 404


def test_unknown_certificate_returns_404(client):
    assert client.get("/api/certificates/9999/download").status_code == 404


def test_zip_contains_only_done_certificates(client, submit_job):
    recipients = GOOD_RECIPIENTS + [{"name": "", "email": "x@example.com"}]
    job_id = submit_job(recipients).get_json()["job_id"]
    rows = certificates_of(client, job_id)

    response = client.get(f"/api/jobs/{job_id}/download")

    assert response.status_code == 200
    assert response.content_type == "application/zip"
    names = zipfile.ZipFile(io.BytesIO(response.data)).namelist()
    assert names == [f"certificate_{rows[0]['id']}.pdf", f"certificate_{rows[1]['id']}.pdf"]


def test_zip_is_404_when_nothing_is_done(client, submit_job):
    job_id = submit_job([{"name": "", "email": "x@example.com"}]).get_json()["job_id"]
    assert client.get(f"/api/jobs/{job_id}/download").status_code == 404
