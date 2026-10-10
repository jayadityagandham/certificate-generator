import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { verifyCertificate } from "../api";

export default function VerifyPage() {
  const { token } = useParams();
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    verifyCertificate(token)
      .then(setResult)
      .catch((err) => setError(err.message));
  }, [token]);

  if (error) return <div className="alert alert-error">{error}</div>;
  if (result === null) return <p className="muted">Checking certificate...</p>;

  if (!result.valid) {
    return (
      <div className="card verify verify-bad">
        <h1>Certificate not found</h1>
        <p>
          This link does not match any issued certificate. Check that you scanned the code on the
          certificate itself.
        </p>
        <Link to="/">Back to home</Link>
      </div>
    );
  }

  return (
    <div className="card verify verify-ok">
      <h1>Valid certificate</h1>
      <dl>
        <dt>Awarded to</dt>
        <dd>{result.recipient_name}</dd>
        <dt>For completing</dt>
        <dd>{result.event_name}</dd>
        <dt>Issued on</dt>
        <dd>{result.issue_date}</dd>
        <dt>Issued by</dt>
        <dd>{result.issuer_name}</dd>
      </dl>
    </div>
  );
}
