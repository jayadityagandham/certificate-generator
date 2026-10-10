import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listJobs } from "../api";
import StatusBadge from "../components/StatusBadge";

export default function JobsPage() {
  const [jobs, setJobs] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    listJobs()
      .then(setJobs)
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <div className="alert alert-error">{error}</div>;
  if (jobs === null) return <p className="muted">Loading jobs...</p>;

  return (
    <>
      <h1>Jobs</h1>
      {jobs.length === 0 ? (
        <p>
          No jobs yet. <Link to="/">Start a new batch</Link> to generate your first certificates.
        </p>
      ) : (
        <div className="card table-wrap">
          <table>
            <thead>
              <tr>
                <th>Job</th>
                <th>Event</th>
                <th>Status</th>
                <th>Done</th>
                <th>Failed</th>
                <th>Pending</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.job_id}>
                  <td>
                    <Link to={"/jobs/" + job.job_id}>#{job.job_id}</Link>
                  </td>
                  <td>{job.event_name}</td>
                  <td>
                    <StatusBadge status={job.status} />
                  </td>
                  <td>{job.done}</td>
                  <td>{job.failed}</td>
                  <td>{job.pending}</td>
                  <td>{new Date(job.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
