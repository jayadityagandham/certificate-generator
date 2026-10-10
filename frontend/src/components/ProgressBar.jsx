// Share of certificates that are finished, whether they succeeded or failed.
export default function ProgressBar({ total, done, failed }) {
  const finished = done + failed;
  const percent = total === 0 ? 0 : Math.round((finished / total) * 100);

  return (
    <div
      className="progress"
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={percent}
      aria-label="Certificates processed"
    >
      <div className="progress-fill" style={{ width: percent + "%" }} />
    </div>
  );
}
