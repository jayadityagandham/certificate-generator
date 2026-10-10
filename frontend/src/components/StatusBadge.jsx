const LABELS = {
  PENDING: "Pending",
  DONE: "Done",
  FAILED: "Failed",
  PROCESSING: "Processing",
  COMPLETED: "Completed",
  COMPLETED_WITH_ERRORS: "Completed with errors",
};

export default function StatusBadge({ status }) {
  return <span className={"badge badge-" + status.toLowerCase()}>{LABELS[status] || status}</span>;
}
