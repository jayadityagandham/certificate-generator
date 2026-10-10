import os

from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import event
from sqlalchemy.engine import Engine

from .models import db
from .routes_api import api


@event.listens_for(Engine, "connect")
def set_sqlite_pragmas(dbapi_connection, connection_record):
    # The background worker writes while request threads read.
    # WAL lets readers and one writer work at the same time, and the busy
    # timeout makes a blocked writer wait (30s) instead of failing at once.
    # This project only uses SQLite, so it is safe to run on every connection.
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.close()


def parse_origins(text):
    origins = []
    for part in text.split(","):
        part = part.strip()
        if part != "":
            origins.append(part)
    return origins


def create_app(test_config=None):
    app = Flask(__name__)
    app.url_map.strict_slashes = False  # /api/jobs and /api/jobs/ both work

    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    instance_dir = os.path.join(backend_dir, "instance")

    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(instance_dir, "app.db"),
        STORAGE_DIR=os.environ.get("STORAGE_DIR", os.path.join(backend_dir, "storage")),
        # BASE_URL is the FRONTEND address: the QR code opens {BASE_URL}/verify/<token>
        BASE_URL=os.environ.get("BASE_URL", "http://localhost:5173").rstrip("/"),
        CORS_ORIGINS=os.environ.get(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ),
        # Tests only: run jobs inline instead of in a background thread.
        SYNC_PROCESSING=False,
    )
    if test_config is not None:
        app.config.update(test_config)

    os.makedirs(instance_dir, exist_ok=True)
    os.makedirs(app.config["STORAGE_DIR"], exist_ok=True)

    CORS(app, resources={r"/api/*": {"origins": parse_origins(app.config["CORS_ORIGINS"])}})

    db.init_app(app)
    with app.app_context():
        db.create_all()

    app.register_blueprint(api)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify(error="Not found"), 404

    return app
