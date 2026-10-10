# EXPLAIN.md: how it works and where to change things

## One request, in plain English

1. **The UI submits.** `frontend/src/pages/SubmitPage.jsx` parses the CSV into a list of `{name, email}` and calls `createJob()` in `api.js`, which POSTs to `/api/jobs`.
2. **Layer 1 validation.** `routes_api.create_job` calls `validation.validate_request`. A bad request gets `400` and stops here. Individual recipients are not looked at yet.
3. **Rows are created.** `services.create_job` saves one `Job` and one `Certificate` per recipient, all `PENDING`. Entries that are not objects are saved as `FAILED` immediately because there is nothing to read.
4. **The server replies at once.** `202` with the job id. Then `processing.start_processing` hands the job to the thread pool.
5. **The worker loop runs.** `processing.process_job` opens its own app context (its own DB session) and `run_job` loops over the pending rows. For each, `process_one` runs `generate_certificate` inside a `try/except`:
   - `validation.validate_recipient` (layer 2). If it returns a message, the row becomes `FAILED` with that message.
   - Otherwise `certificate_renderer.render_certificate` writes `storage/<job_id>/<certificate_id>.pdf`, and the row becomes `DONE`.
   - If anything raises, the `except` rolls back and `mark_failed` stores the error. The loop continues with the next row.
6. **The UI polls.** `JobDetailPage.jsx` calls `GET /api/jobs/<id>` and `/certificates` every 2 seconds. `services.job_summary` counts rows by status and derives the job status. Polling stops when `pending` is 0.
7. **Download.** Single PDF at `/api/certificates/<id>/download`, or a ZIP at `/api/jobs/<id>/download`.
8. **Verify.** The QR code opens `{BASE_URL}/verify/<token>`. `VerifyPage.jsx` calls `/api/verify/<token>`, which answers only for `DONE` certificates.

## If the interviewer asks me to change X, edit this

| Change | Where |
|---|---|
| Add a field to the certificate (e.g. `course_name`) | `SubmitPage.jsx` (state + payload), `validation.validate_request` (if required), `models.Job` (new column), `services.create_job` and `job_summary`, `processing.generate_certificate` (pass it on), `certificate_renderer.render_certificate` (new parameter + draw it), `tests/conftest.py` `make_payload`. Delete `backend/instance/app.db` because there are no migrations. |
| Retry failed certificates | Add a route in `routes_api.py` that sets the job's `FAILED` rows back to `PENDING` and calls `start_processing`. `run_job` already only picks up `PENDING` rows, so nothing else changes. Rows that failed validation will fail again unless the data is fixed. |
| Add a new status | Constants in `models.py`, `services.count_by_status` and `derive_status`, `StatusBadge.jsx` `LABELS`, and the badge colours in `styles.css`. |
| Switch to Celery | In `processing.start_processing`, replace `executor.submit(...)` with a Celery task that builds the app and calls `process_job`. Run a worker process, and move from SQLite to Postgres. The routes and the loop do not change. |
| Support Excel upload | Easiest: parse the file in `SubmitPage.jsx` (e.g. SheetJS) into the same recipient list. Or add an endpoint in `routes_api.py` that reads the file with `openpyxl`, builds the list, and calls `services.create_job`. |
| Change the certificate design | `certificate_renderer.py` only. |
| Change the recipient rules (name length, email check) | `validation.validate_recipient`, plus `tests/test_validation.py`. |
| Change the 1000 limit | `validation.MAX_RECIPIENTS`. |
| Change the polling interval | `POLL_INTERVAL_MS` in `JobDetailPage.jsx`. |
| Add a page | New file in `frontend/src/pages/`, a `Route` in `App.jsx`, a nav link if needed, and a function in `api.js`. |
| Change where PDFs are stored | `STORAGE_DIR` env var, or `processing.pdf_path`. |

## Questions I should be ready for

1. **Why threads and not Celery?** The brief needs bulk handling with a status flow, and a reviewer should run it in two commands. All state is in the database, so swapping in a queue is a change in one function. The cost is that jobs are lost on restart.
2. **What does `with app.app_context()` do in the worker?** A thread has no request, so it has no database session. The app context gives it its own session. Sharing the request's session across threads is unsafe, and it is already closed once the response is sent.
3. **How is one failure kept from stopping the rest?** Each certificate runs in its own `try/except` inside the loop. The handler rolls back, records the error on that row, and the loop moves on.
4. **Why create all rows up front and derive the status?** Progress is a count of rows, so there is nothing to keep in sync. A stored job status could disagree with its rows after a crash.
5. **What happens if the server restarts mid-job?** Rows still `PENDING` stay pending and are not resumed. The fix is a durable queue (Celery/RQ), or a startup task that re-queues `PENDING` rows.
6. **How would someone forge a verification link?** They would have to guess a 128-bit random token. For stronger guarantees I would sign tokens with HMAC and add expiry and revocation.
7. **Why SQLite settings like WAL and a busy timeout?** The worker writes while the UI polls. WAL lets readers and one writer coexist, and the timeout makes a blocked writer wait instead of failing.
