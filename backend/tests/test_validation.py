import pytest

from app.validation import validate_recipient

from conftest import GOOD_RECIPIENTS


def test_empty_recipient_list_is_rejected(submit_job):
    response = submit_job([])
    assert response.status_code == 400
    assert "recipients must not be empty" in response.get_json()["details"]


def test_more_than_1000_recipients_is_rejected(submit_job):
    recipients = []
    for number in range(1001):
        recipients.append({"name": "A", "email": "a@example.com"})
    assert submit_job(recipients).status_code == 400


def test_recipients_must_be_a_list(submit_job):
    assert submit_job("not a list").status_code == 400


@pytest.mark.parametrize(
    "overrides",
    [
        {"event_name": ""},
        {"event_name": None},
        {"issuer_name": "   "},
        {"issue_date": ""},
        {"issue_date": "10-10-2026"},
        {"issue_date": "2026-02-30"},
        {"event_name": "x" * 201},
    ],
)
def test_bad_top_level_fields_are_rejected(submit_job, overrides):
    response = submit_job(GOOD_RECIPIENTS, **overrides)
    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid request"


def test_missing_field_is_rejected(client):
    response = client.post("/api/jobs", json={"recipients": GOOD_RECIPIENTS})
    assert response.status_code == 400
    assert len(response.get_json()["details"]) == 3


def test_body_that_is_not_json_is_rejected(client):
    response = client.post("/api/jobs", data="nope", content_type="text/plain")
    assert response.status_code == 400


def test_recipient_rules():
    assert validate_recipient("Asha Rao", "asha@example.com") is None
    assert validate_recipient("", "asha@example.com") == "name is required"
    assert validate_recipient("   ", "asha@example.com") == "name is required"
    assert "too long" in validate_recipient("A" * 101, "asha@example.com")
    assert validate_recipient("Asha", "") == "email is required"
    assert "not a valid email" in validate_recipient("Asha", "not-an-email")


def test_bad_recipient_does_not_reject_the_request(client, submit_job):
    response = submit_job(
        [
            {"name": "", "email": "a@example.com"},
            {"name": "Good Person", "email": "good@example.com"},
        ]
    )
    assert response.status_code == 202
    job = client.get(f"/api/jobs/{response.get_json()['job_id']}").get_json()
    assert job["done"] == 1
    assert job["failed"] == 1
    assert job["failures"][0]["error"] == "name is required"


def test_oddly_shaped_recipients_never_cause_a_500(client, submit_job):
    response = submit_job(
        [
            123,  # not an object
            {"name": None, "email": "a@example.com"},
            {"name": "Ok Name", "email": 5},
            {"name": ["list"], "email": "b@example.com"},
            {"name": "Good Person", "email": "good@example.com"},
        ]
    )
    assert response.status_code == 202

    job_id = response.get_json()["job_id"]
    job = client.get(f"/api/jobs/{job_id}").get_json()
    assert job["done"] == 1
    assert job["failed"] == 4

    errors = []
    for failure in job["failures"]:
        errors.append(failure["error"])
    assert "recipient entry is not an object" in errors
    assert "name is required" in errors
    assert "email is required" in errors
