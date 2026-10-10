from app import services
from app.models import STATUS_PENDING, Certificate

from conftest import GOOD_RECIPIENTS


def test_create_job_returns_202_with_a_ticket(submit_job):
    response = submit_job(GOOD_RECIPIENTS)
    body = response.get_json()

    assert response.status_code == 202
    assert body["total"] == 2
    assert body["status"] == "PROCESSING"
    assert body["job_id"] >= 1


def test_all_rows_are_created_pending_before_processing(app, make_payload):
    with app.app_context():
        job = services.create_job(make_payload(GOOD_RECIPIENTS))
        rows = Certificate.query.filter_by(job_id=job.id).all()

        assert len(rows) == 2
        tokens = set()
        for row in rows:
            assert row.status == STATUS_PENDING
            tokens.add(row.verification_token)
        assert len(tokens) == 2  # every certificate has its own token


def test_one_request_can_hold_many_recipients(submit_job):
    recipients = []
    for number in range(60):
        recipients.append({"name": f"Person {number}", "email": f"p{number}@example.com"})

    response = submit_job(recipients)

    assert response.status_code == 202
    assert response.get_json()["total"] == 60
