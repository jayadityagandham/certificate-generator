import pytest

from app import create_app

GOOD_RECIPIENTS = [
    {"name": "Asha Rao", "email": "asha@example.com"},
    {"name": "Vikram Singh", "email": "vikram@example.com"},
]


@pytest.fixture
def app(tmp_path):
    # Fresh database file and storage folder for every test.
    return create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path}/test.db",
            "STORAGE_DIR": f"{tmp_path}/storage",
            "SYNC_PROCESSING": True,  # jobs run inline, so tests are deterministic
            "BASE_URL": "http://localhost:5173",
        }
    )


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_payload():
    def build(recipients, **overrides):
        payload = {
            "event_name": "Python Workshop",
            "issue_date": "2026-10-10",
            "issuer_name": "Tech Club",
            "recipients": recipients,
        }
        payload.update(overrides)
        return payload

    return build


@pytest.fixture
def submit_job(client, make_payload):
    def submit(recipients, **overrides):
        return client.post("/api/jobs", json=make_payload(recipients, **overrides))

    return submit
