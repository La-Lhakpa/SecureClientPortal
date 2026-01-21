import { useEffect, useState } from "react";
import { apiClient } from "../api";

function OwnerDashboard({ user }) {
  const [files, setFiles] = useState([]);
  const [users, setUsers] = useState([]);
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  const loadData = async () => {
    const list = await apiClient.get("/files");
    setFiles(list);
    const allUsers = await apiClient.get("/users"); // optional endpoint not existing; fallback.
    setUsers(allUsers || []);
  };

  useEffect(() => {
    loadData().catch(() => {});
  }, []);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    setStatus("Uploading...");
    const formData = new FormData();
    formData.append("upload", file);
    try {
      await apiClient.upload("/files/upload", formData);
      setStatus("Uploaded!");
      setFile(null);
      await loadData();
    } catch (err) {
      setError(err.message);
    } finally {
      setTimeout(() => setStatus(""), 1000);
    }
  };

  const handleAssign = async (fileId, clientId) => {
    try {
      await apiClient.post(`/files/${fileId}/assign`, { client_id: clientId });
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="grid">
      <div className="card">
        <h3>Upload a file</h3>
        <form onSubmit={handleUpload} className="form">
          <input type="file" onChange={(e) => setFile(e.target.files[0])} />
          <button type="submit">Upload</button>
          {status && <div className="success">{status}</div>}
          {error && <div className="error">{error}</div>}
        </form>
      </div>

      <div className="card">
        <h3>Files</h3>
        <div className="list">
          {files.map((f) => (
            <div key={f.id} className="list-item">
              <div>
                <div className="title">{f.filename}</div>
                <div className="muted small">Assigned to: {f.client_id || "Unassigned"}</div>
              </div>
              <div className="actions">
                <select onChange={(e) => handleAssign(f.id, e.target.value)} defaultValue="">
                  <option value="" disabled>
                    Assign to client
                  </option>
                  {users
                    .filter((u) => u.role === "CLIENT")
                    .map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.email}
                      </option>
                    ))}
                </select>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default OwnerDashboard;
