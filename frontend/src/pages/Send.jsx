import { useEffect, useState } from "react";
import { apiClient } from "../api";

function Send() {
  const [clients, setClients] = useState([]);
  const [clientId, setClientId] = useState("");
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    apiClient
      .get("/users/clients")
      .then((res) => setClients(res))
      .catch((err) => setError(err.message));
  }, []);

  const handleSend = async (e) => {
    e.preventDefault();
    setError("");
    setStatus("");
    setProgress(0);
    if (!clientId || !file) return;
    try {
      await apiClient.sendFile({ clientId, file, onProgress: setProgress });
      setStatus("Sent successfully.");
      setFile(null);
      setClientId("");
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="grid">
      <div className="card">
        <h3>Send a file</h3>
        <p className="muted">Pick a client, choose a file, and send securely.</p>
        <form className="form" onSubmit={handleSend}>
          <label>Recipient (Client)</label>
          <select value={clientId} onChange={(e) => setClientId(e.target.value)} required>
            <option value="" disabled>
              Select a client
            </option>
            {clients.map((c) => (
              <option key={c.id} value={c.id}>
                {c.email}
              </option>
            ))}
          </select>

          <label>File</label>
          <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} required />

          <button type="submit">Send</button>

          {progress > 0 && progress < 100 && (
            <div className="muted small">Uploading… {progress}%</div>
          )}
          {status && <div className="success">{status}</div>}
          {error && <div className="error">{error}</div>}
        </form>
      </div>
    </div>
  );
}

export default Send;

