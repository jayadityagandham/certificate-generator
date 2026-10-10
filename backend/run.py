import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # use_reloader is OFF on purpose: the reloader restarts the whole process
    # whenever a file changes, and that would kill any background job that is
    # still generating certificates. Debug mode is opt-in: FLASK_DEBUG=1.
    debug = os.environ.get("FLASK_DEBUG") == "1"
    app.run(host="127.0.0.1", port=5000, debug=debug, use_reloader=False)
