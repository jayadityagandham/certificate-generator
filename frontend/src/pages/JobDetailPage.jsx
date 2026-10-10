import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { certificateDownloadUrl, getCertificates, getJob, jobZipUrl } from "../api";
import ProgressBar from "../components/ProgressBar";
import StatusBadge from "../components/StatusBadge";

const POLL_INTERVAL_MS = 2000;

export default function JobDetailPage() {
  const { id } = useParams();
  const [job, setJob] = useState(null);
  const [certificates, setCertificates] = useState([]);
  const [error, setError] = useState("");

  // Polling: ask the server for fresh numbers every 2 seconds until nothing is
  // pending, then stop. The cleanup function stops the timer when the page is left.
  useEffect(() => {
    let stopped = false;
    let timer = null;

    function stopPolling() {
      clearInterval(timer);
    }

    async function load() {
      try {
        const [jobData, certificateData] = await Promise.all([getJob(id), getCertificates(id)]);
        if (stopped) return;
        setJob(jobData);
        setCertificates(certificateData);
        setError("");
        if (jobData.pending === 0) {
          stopPolling();
        }
      } catch (err) {
        if (stopped) return;
        setError(err.message);
        if (err.status === 404) {
          stopPolling();
        }
      }
    }

    load();
    timer = setInterval(load, POLL_INTERVAL_MS);

    return () => {
      stopped = true;
      stopPolling();
    };
  }, [id]);

  if (error && job === null) return <div className="alert alert-error">{error}</div>;
  if (job === null) return <p className="muted">Loading job...</p>;

  return (
    <>
      <p className="crumb">
        <Link to="/jobs">Jobs</Link> / Job #{job.job_id}
      </p>

      <div className="job-head">
        <div>
          <h1>{job.event_name}</h1>
          <p className="muted">
            Issued by {job.issuer_name} on {job.issue_date}
          </p>
        </div>
        <StatusBadge status={job.status} />
      </div>

      {error && <div className="alert alert-error">Connection problem: {error}. Retrying...</div>}

      <div className="card">
        <ProgressBar total={job.total} done={job.done} failed={job.failed} />
        <div className="stats">
          <span>{job.total} total</span>
          <span className="stat-done">{job.done} done</span>
          <span className="stat-failed">{job.failed} failed</span>
          <span className="stat-pending">{job.pending} pending</span>
        </div>
        <div className="actions">
          {job.done > 0 ? (
            <a className="btn btn-primary" href={jobZipUrl(job.job_id)}>
              Download all as ZIP
            </a>
          ) : (
            <span className="muted">Downloads appear as certificates finish.</span>
          )}
        </div>
      </div>

      <div className="card table-wrap">
        <table>
          <thead>
            <tr>
              <th>Recipient</th>
              <th>Status</th>
              <th>Details</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {certificates.map((cert) => (
              <tr key={cert.id}>
                <td>
                  <div>{cert.recipient_name || <em className="muted">(no name)</em>}</div>
                  <div className="muted small">{cert.recipient_email}</div>
                </td>
                <td>
                  <StatusBadge status={cert.status} />
                </td>
                <td className={cert.status === "FAILED" ? "error-text" : "muted"}>
                  {cert.status === "FAILED" && cert.error}
                  {cert.status === "PENDING" && "Waiting to be generated"}
                  {cert.status === "DONE" && "Certificate ready"}
                </td>
                <td>
                  {cert.status === "DONE" && (
                    <span className="row-actions">
                      <a href={certificateDownloadUrl(cert.id)}>Download</a>
                      <Link to={"/verify/" + cert.verification_token}>Verify</Link>
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
