import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listJobs } from "../api";
import StatusBadge from "../components/StatusBadge";

const FILTERS = [
  { key: "all", label: "Total" },
  { key: "succeeded", label: "Succeeded" },
  { key: "failed", label: "Failed" },
  { key: "pending", label: "Pending" },
];

function matchesFilter(job, filter) {
  if (filter === "succeeded") return job.status === "COMPLETED";
  if (filter === "failed") return job.status === "COMPLETED_WITH_ERRORS";
  if (filter === "pending") return job.status === "PROCESSING";
  return true;
}

export default function JobsPage() {
  const [jobs, setJobs] = useState(null);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    listJobs()
      .then(setJobs)
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <div className="alert alert-error">{error}</div>;
  if (jobs === null) return <p className="muted">Loading jobs...</p>;

  const counts = {
    all: jobs.length,
    succeeded: jobs.filter((job) => job.status === "COMPLETED").length,
    failed: jobs.filter((job) => job.status === "COMPLETED_WITH_ERRORS").length,
    pending: jobs.filter((job) => job.status === "PROCESSING").length,
  };
  const filteredJobs = jobs.filter((job) => matchesFilter(job, filter));

  return (
    <>
      <h1>Jobs</h1>
      {jobs.length === 0 ? (
        <p>
          No jobs yet. <Link to="/">Start a new batch</Link> to generate your first certificates.
        </p>
      ) : (
        <>
          <div className="job-filters" aria-label="Filter jobs">
            {FILTERS.map((item) => (
              <button
                key={item.key}
                type="button"
                className={"filter-button" + (filter === item.key ? " active" : "")}
                aria-pressed={filter === item.key}
                onClick={() => setFilter(item.key)}
              >
                <span>{item.label}</span>
                <strong>{counts[item.key]}</strong>
              </button>
            ))}
          </div>

          {filteredJobs.length === 0 ? (
            <p className="muted">No jobs match the selected filter.</p>
          ) : (
            <div className="card table-wrap">
              <table>
                <thead className="table-header">
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
                  {filteredJobs.map((job) => (
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
      )}
    </>
  );
}
