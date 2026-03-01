import { useState } from "react";
// DEV ONLY — REMOVE WHEN BACKEND AUTH IS READY
import { MOCK_RECIPIENTS } from "../constants/mockData";

function Send() {
  const [recipient, setRecipient] = useState("");
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  const handleSend = (e) => {
    e.preventDefault();
    setError("");
    setStatus("");

    // Validate recipient and file
    if (!recipient) {
      setError("Please select a recipient");
      return;
    }
    if (!file) {
      setError("Please select a file");
      return;
    }

    // DEV ONLY — REMOVE WHEN BACKEND AUTH IS READY
    // Show success message (no backend call yet)
    setStatus("DEV MODE: File queued for sending");
    setFile(null);
    setRecipient("");
    
    // Clear status after 3 seconds
    setTimeout(() => setStatus(""), 3000);
  };

  return (
    <div className="send-page">
      <div className="send-container">
        <h1 className="send-title">Send a File</h1>
        <form className="send-form" onSubmit={handleSend}>
          <div className="form-group">
            <label htmlFor="recipient" className="form-label">
              Recipient 
            </label>
            <select
              id="recipient"
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
              className="form-select"
            >
              <option value="" disabled>
                Select a recipient
              </option>
              {/* DEV ONLY — REMOVE WHEN BACKEND AUTH IS READY */}
              {MOCK_RECIPIENTS.map((email) => (
                <option key={email} value={email}>
                  {email}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="file" className="form-label">
              File
            </label>
            <input
              id="file"
              type="file"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="form-file"
              accept="*/*"
            />
            {file && (
              <div className="file-info">
                Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
              </div>
            )}
          </div>

          <button type="submit" className="send-button">
            Send
          </button>

          {status && <div className="send-success">{status}</div>}
          {error && <div className="send-error">{error}</div>}
        </form>
      </div>
    </div>
  );
}

export default Send;
