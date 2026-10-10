from app import certificate_renderer


def test_one_certificate_failing_does_not_stop_the_others(client, submit_job, monkeypatch):
    real_render = certificate_renderer.render_certificate

    def flaky_render(**kwargs):
        if kwargs["recipient_name"] == "Boom":
            raise RuntimeError("renderer exploded")
        return real_render(**kwargs)

    monkeypatch.setattr(certificate_renderer, "render_certificate", flaky_render)

    response = submit_job(
        [
            {"name": "First Person", "email": "first@example.com"},
            {"name": "Boom", "email": "boom@example.com"},
            {"name": "Third Person", "email": "third@example.com"},
        ]
    )
    job = client.get(f"/api/jobs/{response.get_json()['job_id']}").get_json()

    assert job["status"] == "COMPLETED_WITH_ERRORS"
    assert (job["done"], job["failed"]) == (2, 1)
    assert job["failures"][0]["recipient_name"] == "Boom"
    assert "renderer exploded" in job["failures"][0]["error"]
