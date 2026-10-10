# Bulk Certificate Generator

A backend API (Flask) with a small React UI that generates certificates for a whole list of
recipients in a single request. Each certificate is a PDF made from one predefined template and
carries a QR code that opens a public verification page.

- **Bulk by design:** one request holds up to 1000 recipients. The API replies immediately with a job id and the work runs in the background.
- **Failure isolation:** every certificate is processed in its own `try/except`. A bad row, or a crash while drawing one PDF, fails only that certificate.
- **Progress tracking:** the job status shows how many certificates are pending, done and failed, with the reason for each failure.
- **Verifiable certificates:** every PDF has a QR code linking to `/verify/<token>`, which confirms the certificate is genuine.

## Screenshots

_Add after running the app locally (see the walkthrough below):_

| New batch | Progress with failures | Verify page |
|---|---|---|
| `docs/screenshot-submit.png` | `docs/screenshot-progress.png` | `docs/screenshot-verify.png` |

A sample output is in [`docs/sample-certificate.pdf`](docs/sample-certificate.pdf).

## Tech stack

| Part | Choice |
|---|---|
| Backend | Python 3.11+, Flask, Flask-SQLAlchemy |
| Database | SQLite (relational, zero setup) |
| PDF and QR | ReportLab, `qrcode` + Pillow |
| Background work | `concurrent.futures.ThreadPoolExecutor` |
| Frontend | React 18, Vite, react-router-dom, papaparse (CSV parsing only) |
| Tests | pytest + Flask test client |

## Project layout

```
backend/
  app/
    __init__.py              app factory, config, CORS, SQLite settings
    models.py                Job and Certificate tables
    validation.py            request-level and recipient-level checks
    services.py              create a job, summarise a job (shared logic)
    processing.py            the background loop: validate -> render -> save result
    certificate_renderer.py  draws one PDF (no database access)
    routes_api.py            all HTTP endpoints
  tests/                     pytest suite
  run.py                     starts the dev server
frontend/
  src/api.js                 the only file that calls the backend
  src/pages/                 New batch, Jobs, Job detail, Verify
docs/sample-certificate.pdf
EXPLAIN.md                   request flow and "where do I change X" table
```

## Quick start

You need Python 3.11+ and Node 18+. Use two terminals.

**Terminal 1: backend (http://localhost:5000)**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

**Terminal 2: frontend (http://localhost:5173)**

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

### Configuration (all optional)

| Variable | Default | Meaning |
|---|---|---|
| `BASE_URL` | `http://localhost:5173` | The **frontend** address. QR codes encode `{BASE_URL}/verify/<token>`. |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated origins allowed to call the API. |
| `STORAGE_DIR` | `backend/storage` | Where PDFs are written. |
| `FLASK_DEBUG` | off | Set to `1` for debug mode. The reloader stays off on purpose (see Design decisions). |
| `VITE_API_URL` | `http://localhost:5000` | Frontend setting: where the API lives (`frontend/.env`). |

## Run the tests

```bash
cd backend
source .venv/bin/activate
python -m pytest
```

The tests use a temporary database and storage folder per test, and turn on the `SYNC_PROCESSING`
config flag so jobs run inline instead of in a background thread. That flag exists **only for
tests**, to make them deterministic. Real use leaves it off.

## 2-minute reviewer walkthrough

1. Open http://localhost:5173 and click **Load sample data**. It fills in 8 recipients including bad rows: an empty name, an invalid email, a 150-character name, a duplicate, and a very long valid name.
2. Click **Generate certificates**. You land on the job page, where the progress bar and counts update every 2 seconds.
3. When it finishes, you should see 5 done and 3 failed. Each failed row shows its reason, and the good certificates were still produced.
4. Click **Download** on a row, or **Download all as ZIP**. Open a PDF: the long name has shrunk to fit.
5. Click **Verify** on a row to see the verification page (the QR code opens the same page).
6. Open **Jobs** to see the job list with counts.

## API

All endpoints return JSON except the downloads. Trailing slashes are optional.

### Submit a job

`POST /api/jobs` returns `202 Accepted`

```bash
curl -X POST http://localhost:5000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "Introduction to Machine Learning",
    "issue_date": "2026-10-10",
    "issuer_name": "Tech Club",
    "recipients": [
      {"name": "Asha Rao", "email": "asha@example.com"},
      {"name": "", "email": "no-name@example.com"}
    ]
  }'
```

```json
{ "job_id": 1, "status": "PROCESSING", "total": 2 }
```

Invalid requests (empty list, more than 1000 recipients, missing fields, bad date) return `400`:

```json
{ "error": "Invalid request", "details": ["recipients must not be empty"] }
```

### Check progress

`GET /api/jobs/{job_id}`

```bash
curl http://localhost:5000/api/jobs/1
```

```json
{
  "job_id": 1, "event_name": "Introduction to Machine Learning",
  "issue_date": "2026-10-10", "issuer_name": "Tech Club",
  "status": "COMPLETED_WITH_ERRORS",
  "total": 2, "pending": 0, "done": 1, "failed": 1,
  "created_at": "2026-10-10T09:30:00Z",
  "failures": [
    { "certificate_id": 2, "recipient_name": "", "error": "name is required" }
  ]
}
```

Job status is **derived** from the certificate rows: `PROCESSING` while anything is pending, `COMPLETED` when all succeeded, `COMPLETED_WITH_ERRORS` otherwise.

### List jobs and certificates

- `GET /api/jobs` returns the 50 most recent jobs, newest first.
- `GET /api/jobs/{job_id}/certificates` returns `[{id, recipient_name, recipient_email, status, error, verification_token}]`.

### Retrieve certificates

```bash
curl -OJ http://localhost:5000/api/certificates/1/download   # one PDF
curl -OJ http://localhost:5000/api/jobs/1/download           # ZIP of all finished PDFs
```

A certificate that is not `DONE` returns `404`. The ZIP returns `404` if nothing has finished yet.

### Verify a certificate

`GET /api/verify/{token}`

```json
{ "valid": true, "recipient_name": "Asha Rao", "event_name": "Introduction to Machine Learning",
  "issue_date": "2026-10-10", "issuer_name": "Tech Club" }
```

Unknown tokens and failed certificates return `404` with `{ "valid": false }`.

### Health

`GET /health` returns `{ "status": "ok" }`.

## How it works

1. **Submit.** The request is checked as a whole (layer 1 validation). The server creates one `Job` row and one `Certificate` row per recipient, all `PENDING`, then replies `202` with the job id.
2. **Background loop.** A worker thread walks the pending rows. For each one it validates the recipient (layer 2), draws the PDF, and marks the row `DONE` or `FAILED` with a reason. Each certificate has its own `try/except`.
3. **Progress.** Asking for a job counts its rows by status. There are no separate counters to keep in sync.
4. **Retrieve.** Download one PDF or a ZIP of all finished ones.
5. **Verify.** Scanning the QR code opens the React page `/verify/<token>`, which calls the API.

## Design decisions

**Background threads, not synchronous, not Celery.**

| Option | Why not / why |
|---|---|
| Synchronous | Simplest, but a 1000-recipient request would block for a long time and risk a timeout. It contradicts "designed around bulk". |
| **ThreadPoolExecutor (chosen)** | Real `202` + polling flow with no extra infrastructure. A reviewer can run it with two commands. |
| Celery/RQ + Redis | The production answer (retries, survives restarts, scales out), but needs a broker and more setup. All state lives in the database, so swapping the executor for a queue is a small change in `start_processing`. |

**Rows are created up front as `PENDING`.** Progress is a count of rows by status, so the numbers can never drift from reality, and the client sees every recipient immediately.

**Job status is derived, not stored.** A stored status could disagree with its rows, for example after a crash. A derived one cannot.

**Two layers of validation.** Layer 1 (whole request) returns `400` for things that make the request meaningless: empty list, too many recipients, missing event name, bad date. Layer 2 (per recipient) records a `FAILED` certificate with a reason and carries on. Recipients stay loose data at layer 1 so one bad entry never rejects the batch. Entries that are not even objects (a number, `null`) become `FAILED` rows with a clear message instead of a `500`.

**The worker opens its own app context and session.** The request's database session is closed once the response is sent and is not safe to share across threads. The worker calls `with app.app_context():` to get its own, and removes it when done.

**SQLite settings for threads.** WAL mode and a 30 second busy timeout are set on every connection, because the worker writes while request threads read. The pool has two workers so SQLite's single writer is not overloaded.

**The dev server runs without the reloader.** The reloader restarts the process on file changes, which would kill a running background job.

**PDFs are named by certificate id** (`storage/<job_id>/<certificate_id>.pdf`), never by recipient name. Names can collide, and user text inside a file path is a path-injection risk. Download filenames are also id-based.

**ReportLab over WeasyPrint.** ReportLab is pure Python with no system libraries, so it installs anywhere. WeasyPrint has nicer HTML templating but needs OS packages, which is a risk on a reviewer's machine.

**QR verification.** Each certificate has a random 128-bit token. The QR code opens a public page that shows the recipient, event, date and issuer. Only `DONE` certificates verify. It answers "is this PDF genuine?", which a plain template cannot.

**Plain React, no UI framework.** The frontend is a thin client: `api.js` is the only file that calls the backend, and the progress page polls with a `useEffect` timer that stops when nothing is pending.

## Known limitations

- Background threads live inside the server process. If the server restarts mid-job, certificates still `PENDING` are not resumed.
- There are no automatic retries and no retry endpoint.
- SQLite allows one writer at a time. Fine for this scale, not for many concurrent jobs.
- There is no authentication: anyone who can reach the API can create jobs and download certificates.
- ReportLab's built-in fonts do not support Indian-language scripts such as Telugu or Hindi. Such names would not render correctly.
- Scanning a QR code from a phone will not open `localhost`. Use the **Verify** link in the UI, or run a tunnel such as ngrok and set `BASE_URL` to the tunnel address.
- Database tables are created with `create_all()`, with no migrations. After changing a model, delete `backend/instance/app.db`.

## Deployment

This project is **not deployed**. It is meant to be run locally, as described above. In
production I would use Postgres instead of SQLite, object storage such as S3 for the PDFs, and a
real queue (Celery or RQ with Redis) so jobs survive restarts and retry. Serverless platforms such
as Vercel are a poor fit for the backend: functions are frozen once the response is sent, so
background work dies, and there is no persistent disk.

## AI usage

Built with AI assistance, which the brief allows. Every file was reviewed and is documented in
[`EXPLAIN.md`](EXPLAIN.md).

## Learnings

- A background thread has no request, so it needs its own app context and database session.
- SQLite can handle a writing worker plus readers if WAL mode and a busy timeout are set.
- Loose input needs explicit handling: decide where a bad value becomes an error row instead of an exception.
- Deriving state from rows is simpler and safer than storing it twice.

## Future scope

- Celery/RQ for durable jobs, retries and horizontal scaling.
- A "retry failed" endpoint, and resuming `PENDING` rows after a restart.
- Unicode fonts for Indian-language names.
- Postgres, object storage, and migrations.
- HMAC-signed verification tokens, plus expiry and revocation.
- Authentication and rate limiting.
- Email delivery of certificates to recipients.
