import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Papa from "papaparse";
import { createJob } from "../api";
import { SAMPLE_CSV } from "../sampleData";

function today() {
  return new Date().toISOString().slice(0, 10);
}

// Turns pasted/uploaded CSV text (header: name,email) into the API's recipient list.
function parseRecipients(csvText) {
  if (csvText.trim() === "") {
    return [];
  }
  const result = Papa.parse(csvText.trim(), {
    header: true,
    skipEmptyLines: true,
    transformHeader: (header) => header.trim().toLowerCase(),
  });
  return result.data.map((row) => ({ name: row.name, email: row.email }));
}

export default function SubmitPage() {
  const navigate = useNavigate();
  const [eventName, setEventName] = useState("");
  const [issueDate, setIssueDate] = useState(today());
  const [issuerName, setIssuerName] = useState("");
  const [csvText, setCsvText] = useState("");
  const [errors, setErrors] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  const recipientCount = parseRecipients(csvText).length;

  async function handleFile(event) {
    const file = event.target.files[0];
    if (file) {
      setCsvText(await file.text());
    }
  }

  function loadSample() {
    setEventName("Introduction to Machine Learning");
    setIssuerName("Tech Club");
    setCsvText(SAMPLE_CSV);
    setErrors([]);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const recipients = parseRecipients(csvText);
    if (recipients.length === 0) {
      setErrors(["Add at least one recipient. Use CSV with a name,email header row."]);
      return;
    }

    setSubmitting(true);
    setErrors([]);
    try {
      const job = await createJob({
        event_name: eventName,
        issue_date: issueDate,
        issuer_name: issuerName,
        recipients,
      });
      navigate("/jobs/" + job.job_id);
    } catch (error) {
      setErrors(error.details.length > 0 ? error.details : [error.message]);
      setSubmitting(false);
    }
  }

  return (
    <>
      <h1>Generate certificates in bulk</h1>
      <p className="lead">
        Fill in the event details, add your recipients, and every valid recipient gets a certificate.
        Invalid rows are reported individually and never block the others.
      </p>

      <form onSubmit={handleSubmit} className="card form">
        <label>
          Event or course name
          <input value={eventName} onChange={(e) => setEventName(e.target.value)} />
        </label>

        <div className="row">
          <label>
            Issue date
            <input type="date" value={issueDate} onChange={(e) => setIssueDate(e.target.value)} />
          </label>
          <label>
            Issued by
            <input value={issuerName} onChange={(e) => setIssuerName(e.target.value)} />
          </label>
        </div>

        <label>
          Recipients (CSV with a name,email header)
          <textarea
            rows={10}
            value={csvText}
            onChange={(e) => setCsvText(e.target.value)}
            placeholder={"name,email\nAsha Rao,asha@example.com"}
            spellCheck={false}
          />
        </label>

        <div className="row row-between">
          <label className="file-label">
            Or upload a .csv file
            <input type="file" accept=".csv,text/csv" onChange={handleFile} />
          </label>
          <span className="muted">
            {recipientCount === 1 ? "1 recipient found" : recipientCount + " recipients found"}
          </span>
        </div>

        {errors.length > 0 && (
          <div className="alert alert-error" role="alert">
            <strong>The request could not be submitted:</strong>
            <ul>
              {errors.map((message) => (
                <li key={message}>{message}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="actions">
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Submitting..." : "Generate certificates"}
          </button>
          <button type="button" className="btn" onClick={loadSample} disabled={submitting}>
            Load sample data
          </button>
        </div>
      </form>
    </>
  );
}
