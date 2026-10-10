from conftest import GOOD_RECIPIENTS


def token_of(client, job_id, index):
    return client.get(f"/api/jobs/{job_id}/certificates").get_json()[index]["verification_token"]


def test_done_certificate_verifies(client, submit_job):
    job_id = submit_job(GOOD_RECIPIENTS).get_json()["job_id"]
    response = client.get(f"/api/verify/{token_of(client, job_id, 0)}")

    assert response.status_code == 200
    assert response.get_json() == {
        "valid": True,
        "recipient_name": "Asha Rao",
        "event_name": "Python Workshop",
        "issue_date": "2026-10-10",
        "issuer_name": "Tech Club",
    }


def test_unknown_token_is_not_valid(client):
    response = client.get("/api/verify/doesnotexist")
    assert response.status_code == 404
    assert response.get_json() == {"valid": False}


def test_failed_certificate_is_not_valid(client, submit_job):
    job_id = submit_job([{"name": "", "email": "x@example.com"}]).get_json()["job_id"]
    response = client.get(f"/api/verify/{token_of(client, job_id, 0)}")

    assert response.status_code == 404
    assert response.get_json() == {"valid": False}
