// The ONLY file that talks to the backend. Every page imports from here.

const API = import.meta.env.VITE_API_URL || "http://localhost:5000";

async function request(path, options) {
  let response;
  try {
    response = await fetch(API + path, options);
  } catch (networkError) {
    throw new Error("Cannot reach the server. Is the backend running on " + API + "?");
  }

  let body = null;
  try {
    body = await response.json();
  } catch (notJson) {
    // Some error responses have no JSON body; that is fine.
  }

  if (!response.ok) {
    const error = new Error(body && body.error ? body.error : "Request failed (" + response.status + ")");
    error.status = response.status;
    error.details = body && body.details ? body.details : [];
    error.body = body;
    throw error;
  }
  return body;
}

export function createJob(payload) {
  return request("/api/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function listJobs() {
  return request("/api/jobs");
}

export function getJob(id) {
  return request("/api/jobs/" + id);
}

export function getCertificates(id) {
  return request("/api/jobs/" + id + "/certificates");
}

export async function verifyCertificate(token) {
  try {
    return await request("/api/verify/" + token);
  } catch (error) {
    // The API answers 404 {"valid": false} for unknown or failed certificates.
    if (error.status === 404) {
      return { valid: false };
    }
    throw error;
  }
}

// Downloads are plain links: the browser handles the file itself.
export function certificateDownloadUrl(certificateId) {
  return API + "/api/certificates/" + certificateId + "/download";
}

export function jobZipUrl(jobId) {
  return API + "/api/jobs/" + jobId + "/download";
}
