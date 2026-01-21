import { useEffect, useState } from "react";
import { apiClient } from "../api";

function ClientDashboard() {
  const [files, setFiles] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    apiClient
      .get("/files")
      .then((res) => setFiles(res))
      .catch((err) => setError(err.message));
  }, []);

  const handleDownload = async (id, filename) => {
    try {
      const url = await apiClient.download(`/files/${id}/download`);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="card">
      <h3>Your files</h3>
      {error && <div className="error">{error}</div>}
      <div className="list">
        {files.map((f) => (
          <div key={f.id} className="list-item">
            <div className="title">{f.filename}</div>
            <button className="secondary" onClick={() => handleDownload(f.id, f.filename)}>
              Download
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ClientDashboard;
