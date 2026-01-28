import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../api";
import { Upload, Download, Send, Inbox, File } from "lucide-react";

function Dashboard({ user }) {
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState(user || null);
  const [users, setUsers] = useState([]);
  const [recipientsLoading, setRecipientsLoading] = useState(false);
  const [selectedReceiver, setSelectedReceiver] = useState("");
  const [file, setFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState("");
  const [sentFiles, setSentFiles] = useState([]);
  const [receivedFiles, setReceivedFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (user) setCurrentUser(user);
  }, [user]);

  // If user prop is not available, fetch it via /me (fallback)
  useEffect(() => {
    if (!currentUser) {
      apiClient
        .get("/me")
        .then((me) => {
          setCurrentUser(me);
        })
        .catch((err) => {
          if (err?.status === 401) {
            setError("Session expired. Please log in again.");
            navigate("/login", { replace: true });
            return;
          }
          setError(err.message || "Failed to load user data");
        });
    }
  }, [currentUser, navigate]);

  useEffect(() => {
    if (currentUser) {
      loadData();
    }
  }, [currentUser]);

  const loadData = async () => {
    try {
      setLoading(true);
      setRecipientsLoading(true);
      const [usersRes, sentRes, receivedRes] = await Promise.all([
        apiClient.get("/users"),
        apiClient.get("/files/sent"),
        apiClient.get("/files/received"),
      ]);
      // Backend already excludes current user, but keep a defensive filter
      const meId = currentUser?.id;
      setUsers(meId ? usersRes.filter((u) => u.id !== meId) : usersRes);
      setSentFiles(sentRes);
      setReceivedFiles(receivedRes);
      setError("");
    } catch (err) {
      if (err?.status === 401) {
        setError("Session expired. Please log in again.");
        navigate("/login", { replace: true });
        return;
      }
      setError(err.message || "Failed to load data");
      console.error("Load error:", err);
    } finally {
      setLoading(false);
      setRecipientsLoading(false);
    }
  };

  const handleSendFile = async (e) => {
    e.preventDefault();
    setError("");
    setUploadStatus("");
    setUploadProgress(0);

    if (!selectedReceiver) {
      setError("Please select a receiver");
      return;
    }
    if (!file) {
      setError("Please select a file");
      return;
    }

    try {
      setUploadStatus("Uploading...");
      await apiClient.sendFile({
        receiverId: parseInt(selectedReceiver),
        file,
        onProgress: (progress) => {
          setUploadProgress(progress);
        },
      });
      setUploadStatus("File sent successfully!");
      setFile(null);
      setSelectedReceiver("");
      setUploadProgress(0);
      // Reload files
      await loadData();
      setTimeout(() => setUploadStatus(""), 3000);
    } catch (err) {
      if (err?.status === 401) {
        setError("Session expired. Please log in again.");
        navigate("/login", { replace: true });
        return;
      }
      setError(err.message || "Failed to send file");
      setUploadStatus("");
      setUploadProgress(0);
    }
  };

  const handleDownload = async (fileId, filename) => {
    try {
      const blobUrl = await apiClient.download(`/files/${fileId}/download`);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    } catch (err) {
      setError(err.message || "Failed to download file");
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getReceiverName = (receiverId) => {
    const receiver = users.find((u) => u.id === receiverId);
    return receiver ? receiver.email : `User ${receiverId}`;
  };

  const getSenderName = (senderId) => {
    if (senderId === currentUser?.id) return "You";
    const sender = users.find((u) => u.id === senderId);
    return sender ? sender.email : `User ${senderId}`;
  };

  if (!currentUser) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-container">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto"></div>
            <p className="mt-4 text-white/70">Loading user data...</p>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-container">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto"></div>
            <p className="mt-4 text-white/70">Loading...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <div className="dashboard-container">
        <h1 className="dashboard-title">File Sharing Dashboard</h1>
        <p className="dashboard-subtitle">Welcome, {currentUser.email}</p>

        {error && (
          <div className="alert alert-error mb-6">
            <p>{error}</p>
          </div>
        )}

        {/* Send File Section */}
        <div className="dashboard-section">
          <h2 className="section-title">
            <Send className="inline mr-2" size={20} />
            Send File
          </h2>
          <form onSubmit={handleSendFile} className="send-form">
            <div className="form-group">
              <label htmlFor="receiver" className="form-label">
                Receiver
              </label>
              <select
                id="receiver"
                value={selectedReceiver}
                onChange={(e) => setSelectedReceiver(e.target.value)}
                className="form-select"
                required
              >
                {recipientsLoading ? (
                  <option value="">Loading recipients…</option>
                ) : users.length === 0 ? (
                  <option value="">No recipients available (create another account).</option>
                ) : (
                  <>
                    <option value="">Select a receiver...</option>
                    {users.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.email}
                      </option>
                    ))}
                  </>
                )}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="file" className="form-label">
                File
              </label>
              <input
                id="file"
                type="file"
                onChange={(e) => setFile(e.target.files[0])}
                className="form-input"
                required
              />
              {file && (
                <p className="mt-2 text-sm text-white/70">
                  Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
                </p>
              )}
            </div>

            {uploadProgress > 0 && (
              <div className="mb-4">
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
                <p className="text-sm text-white/70 mt-2">{uploadProgress}%</p>
              </div>
            )}

            {uploadStatus && (
              <div className={`alert ${uploadStatus.includes("success") ? "alert-success" : "alert-info"} mb-4`}>
                <p>{uploadStatus}</p>
              </div>
            )}

            <button
              type="submit"
              className="btn btn-primary"
              disabled={
                uploadProgress > 0 ||
                recipientsLoading ||
                users.length === 0 ||
                !selectedReceiver ||
                !file
              }
            >
              <Upload className="inline mr-2" size={18} />
              Send File
            </button>
          </form>
        </div>

        {/* Sent Files Section */}
        <div className="dashboard-section">
          <h2 className="section-title">
            <Send className="inline mr-2" size={20} />
            Sent Files ({sentFiles.length})
          </h2>
          {sentFiles.length === 0 ? (
            <p className="text-white/50">No files sent yet.</p>
          ) : (
            <div className="files-list">
              {sentFiles.map((f) => (
                <div key={f.id} className="file-item">
                  <File className="inline mr-2" size={18} />
                  <div className="file-info">
                    <p className="file-name">{f.original_filename}</p>
                    <p className="file-meta">
                      To: {f.receiver?.email || getReceiverName(f.receiver_id)} • {formatFileSize(f.size_bytes)} • {formatDate(f.created_at)}
                    </p>
                  </div>
                  <button
                    onClick={() => handleDownload(f.id, f.original_filename)}
                    className="btn btn-secondary btn-sm"
                  >
                    <Download size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Received Files Section */}
        <div className="dashboard-section">
          <h2 className="section-title">
            <Inbox className="inline mr-2" size={20} />
            Received Files ({receivedFiles.length})
          </h2>
          {receivedFiles.length === 0 ? (
            <p className="text-white/50">No files received yet.</p>
          ) : (
            <div className="files-list">
              {receivedFiles.map((f) => (
                <div key={f.id} className="file-item">
                  <File className="inline mr-2" size={18} />
                  <div className="file-info">
                    <p className="file-name">{f.original_filename}</p>
                    <p className="file-meta">
                      From: {f.sender?.email || getSenderName(f.sender_id)} • {formatFileSize(f.size_bytes)} • {formatDate(f.created_at)}
                    </p>
                  </div>
                  <button
                    onClick={() => handleDownload(f.id, f.original_filename)}
                    className="btn btn-secondary btn-sm"
                  >
                    <Download size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
