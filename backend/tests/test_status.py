from app import services
from app.models import Certificate, db

from conftest import GOOD_RECIPIENTS


def test_status_is_completed_when_everything_succeeds(client, submit_job):
    job_id = submit_job(GOOD_RECIPIENTS).get_json()["job_id"]
    job = client.get(f"/api/jobs/{job_id}").get_json()

    assert job["status"] == "COMPLETED"
    assert (job["total"], job["pending"], job["done"], job["failed"]) == (2, 0, 2, 0)
    assert job["failures"] == []


def test_status_is_completed_with_errors_when_some_fail(client, submit_job):
    recipients = GOOD_RECIPIENTS + [{"name": "", "email": "x@example.com"}]
    job_id = submit_job(recipients).get_json()["job_id"]
    job = client.get(f"/api/jobs/{job_id}").get_json()

    assert job["status"] == "COMPLETED_WITH_ERRORS"
    assert (job["total"], job["done"], job["failed"]) == (3, 2, 1)


def test_status_is_processing_while_rows_are_pending(app, make_payload):
    with app.app_context():
        job = services.create_job(make_payload(GOOD_RECIPIENTS))
        summary = services.job_summary(job)

        assert summary["status"] == "PROCESSING"
        assert (summary["pending"], summary["done"], summary["failed"]) == (2, 0, 0)

        # Finish one row by hand: progress is just a count of row statuses.
        first = Certificate.query.filter_by(job_id=job.id).first()
        first.status = "DONE"
        db.session.commit()
        summary = services.job_summary(job)
        assert (summary["pending"], summary["done"]) == (1, 1)
        assert summary["status"] == "PROCESSING"


def test_unknown_job_returns_404(client):
    assert client.get("/api/jobs/9999").status_code == 404


def test_job_list_shows_newest_first(client, submit_job):
    first = submit_job(GOOD_RECIPIENTS).get_json()["job_id"]
    second = submit_job(GOOD_RECIPIENTS).get_json()["job_id"]
    jobs = client.get("/api/jobs").get_json()

    assert jobs[0]["job_id"] == second
    assert jobs[1]["job_id"] == first
