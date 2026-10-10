import os

from app.models import STATUS_DONE, Certificate


def test_pdf_is_created_and_named_by_certificate_id(app, submit_job):
    job_id = submit_job([{"name": "Asha Rao", "email": "asha@example.com"}]).get_json()["job_id"]

    with app.app_context():
        cert = Certificate.query.filter_by(job_id=job_id).one()

        assert cert.status == STATUS_DONE
        assert os.path.exists(cert.file_path)
        assert os.path.basename(cert.file_path) == f"{cert.id}.pdf"
        assert os.path.basename(os.path.dirname(cert.file_path)) == f"{job_id}"
        with open(cert.file_path, "rb") as pdf_file:
            assert pdf_file.read(4) == b"%PDF"


def test_duplicate_recipients_get_separate_files(app, submit_job):
    same = {"name": "Priya Nair", "email": "priya@example.com"}
    job_id = submit_job([same, same]).get_json()["job_id"]

    with app.app_context():
        rows = Certificate.query.filter_by(job_id=job_id).all()
        paths = set()
        for cert in rows:
            assert cert.status == STATUS_DONE
            paths.add(cert.file_path)
        assert len(paths) == 2  # ids never collide, names could


def test_very_long_name_still_renders(app, submit_job):
    long_name = "Venkata Subrahmanyam Raghavendra Chandrasekhar Iyer Kothapalli Narasimha"
    job_id = submit_job([{"name": long_name, "email": "v@example.com"}]).get_json()["job_id"]

    with app.app_context():
        cert = Certificate.query.filter_by(job_id=job_id).one()
        assert cert.status == STATUS_DONE
