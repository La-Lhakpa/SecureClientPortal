import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient, getTransferToken, setTransferToken } from "../api";
import { Upload, Download, Send, Inbox, File, Eye, EyeOff, Copy, Sparkles, Trash2 } from "lucide-react";

function Dashboard({ user }) {
  const navigate = useNavigate();
  const receivedRef = useRef(null);
  const [currentUser, setCurrentUser] = useState(user || null);
  const [users, setUsers] = useState([]);
  const [recipientsLoading, setRecipientsLoading] = useState(false);
  const [selectedReceiver, setSelectedReceiver] = useState("");
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [accessCode, setAccessCode] = useState("");
  const [generatedCode, setGeneratedCode] = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState("");
  const [sentTransfers, setSentTransfers] = useState([]);
  const [receivedTransfers, setReceivedTransfers] = useState([]);
  const [transferFiles, setTransferFiles] = useState({}); // transferId -> files[]
  const [expandedTransferIds, setExpandedTransferIds] = useState(new Set());
  const [incomingCount, setIncomingCount] = useState(0);
  const [showIncomingModal, setShowIncomingModal] = useState(false);
  const [verifyModal, setVerifyModal] = useState({ open: false, transferId: null, error: "" });
  const [verifyCode, setVerifyCode] = useState("");
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
      // show incoming popup count after login/dashboard mount
      apiClient
        .incomingTransfersCount()
        .then((res) => {
          const count = res?.count || 0;
          setIncomingCount(count);
          if (count > 0) setShowIncomingModal(true);
        })
        .catch(() => {
          // non-blocking
        });
    }
  }, [currentUser]);

  const loadData = async () => {
    try {
      setLoading(true);
      setRecipientsLoading(true);
      const [usersRes, sentT, receivedT] = await Promise.all([
        apiClient.get("/users"),
        apiClient.get("/transfers/sent"),
        apiClient.get("/transfers/received"),
      ]);
      // Backend already excludes current user, but keep a defensive filter
      const meId = currentUser?.id;
      setUsers(meId ? usersRes.filter((u) => u.id !== meId) : usersRes);
      setSentTransfers(sentT || []);
      setReceivedTransfers(receivedT || []);
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

  const generateClientCode = () => {
    const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    let out = "";
    for (let i = 0; i < 8; i++) out += alphabet[Math.floor(Math.random() * alphabet.length)];
    setGeneratedCode(out);
    setAccessCode(out);
  };

  const copyCode = async () => {
    const code = accessCode || generatedCode;
    if (!code) return;
    try {
      await navigator.clipboard.writeText(code);
      setUploadStatus("Code copied. Share it securely with the receiver.");
      setTimeout(() => setUploadStatus(""), 2500);
    } catch {
      // ignore
    }
  };

  const handleSendTransfer = async (e) => {
    e.preventDefault();
    setError("");
    setUploadStatus("");
    setUploadProgress(0);

    if (!selectedReceiver) {
      setError("Please select a receiver");
      return;
    }
    const code = (accessCode || "").trim();
    if (!code) {
      setError("Please generate an access code (or enter one) before sending.");
      return;
    }
    if (code.length < 6) {
      setError("Access code must be at least 6 characters.");
      return;
    }
    if (!selectedFiles || selectedFiles.length === 0) {
      setError("Please select at least one file");
      return;
    }

    try {
      setUploadStatus("Uploading...");
      const res = await apiClient.sendTransfer({
        receiverId: parseInt(selectedReceiver),
        accessCode: code,
        files: selectedFiles,
        onProgress: (progress) => {
          setUploadProgress(progress);
        },
      });
      const serverCode = res?.generated_access_code;
      const transferId = res?.transfer_id;
      if (serverCode) {
        setGeneratedCode(serverCode);
        setAccessCode(serverCode);
      }
      setUploadStatus(
        `Transfer sent successfully (ID: ${transferId}). Share the access code with the receiver securely.`
      );
      setSelectedFiles([]);
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

  const toggleExpand = async (transferId, isReceiver, status) => {
    const next = new Set(expandedTransferIds);
    if (next.has(transferId)) {
      next.delete(transferId);
      setExpandedTransferIds(next);
      return;
    }
    next.add(transferId);
    setExpandedTransferIds(next);

    // Fetch files list if allowed
    try {
      const token = isReceiver ? getTransferToken(transferId) : null;
      // If receiver and not opened yet, don't fetch files until verified
      if (isReceiver && status !== "opened") return;
      const files = await apiClient.getTransferFiles(transferId, token);
      setTransferFiles((prev) => ({ ...prev, [transferId]: files }));
    } catch (err) {
      if (err?.status === 401) {
        setError("Session expired. Please log in again.");
        navigate("/login", { replace: true });
        return;
      }
      // receiver not verified yet
      setError(err.message || "Unable to load transfer files");
    }
  };

  const openVerifyModal = (transferId) => {
    setVerifyCode("");
    setVerifyModal({ open: true, transferId, error: "" });
  };

  const submitVerify = async () => {
    const transferId = verifyModal.transferId;
    if (!transferId) return;
    setVerifyModal((p) => ({ ...p, error: "" }));
    try {
      const res = await apiClient.verifyTransfer(transferId, verifyCode.trim());
      const ttoken = res?.transfer_access_token;
      if (ttoken) setTransferToken(transferId, ttoken);
      // Update UI status to opened and refresh list/files
      setReceivedTransfers((prev) =>
        prev.map((t) => (t.transfer_id === transferId ? { ...t, status: "opened" } : t))
      );
      setVerifyModal({ open: false, transferId: null, error: "" });
      // fetch files after verify
      const files = await apiClient.getTransferFiles(transferId, ttoken);
      setTransferFiles((prev) => ({ ...prev, [transferId]: files }));
      const next = new Set(expandedTransferIds);
      next.add(transferId);
      setExpandedTransferIds(next);
      // update incoming count
      apiClient.incomingTransfersCount().then((r) => setIncomingCount(r?.count || 0)).catch(() => {});
    } catch (err) {
      // If the user's JWT is actually missing/expired, redirect to login.
      if (
        err?.status === 401 &&
        typeof err?.message === "string" &&
        (err.message.includes("Invalid or expired token") ||
          err.message.includes("User not found") ||
          err.message.includes("Not authenticated"))
      ) {
        setError("Session expired. Please log in again.");
        navigate("/login", { replace: true });
        return;
      }
      setVerifyModal((p) => ({ ...p, error: err.message || "Invalid code" }));
    }
  };

  const handleDownloadTransferFile = async (transferId, fileId, filename, isReceiver) => {
    try {
      const ttoken = isReceiver ? getTransferToken(transferId) : null;
      const blobUrl = await apiClient.downloadTransfer({
        urlPath: `/transfers/${transferId}/files/${fileId}/download`,
        transferToken: ttoken,
      });
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

  const handleDownloadTransferZip = async (transferId, isReceiver) => {
    try {
      const ttoken = isReceiver ? getTransferToken(transferId) : null;
      const blobUrl = await apiClient.downloadTransfer({
        urlPath: `/transfers/${transferId}/download-all`,
        transferToken: ttoken,
      });
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = `transfer_${transferId}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    } catch (err) {
      setError(err.message || "Failed to download zip");
    }
  };

  const handleDeleteTransferFile = async (transferId, fileId, isReceiver) => {
    try {
      const ttoken = isReceiver ? getTransferToken(transferId) : null;
      const res = await apiClient.deleteTransferFile(transferId, fileId, ttoken);

      // Refresh file list for THIS user; note deletion is per-side now.
      // If you deleted your last visible file, the transfer will disappear from your list
      // (but remain for the other side).
      try {
        const files = await apiClient.getTransferFiles(transferId, ttoken);
        setTransferFiles((prev) => ({ ...prev, [transferId]: files }));
      } catch {
        // If list fails (e.g., no visible files), clear local state for this transfer.
        setTransferFiles((prev) => {
          const next = { ...prev };
          delete next[transferId];
          return next;
        });
      }
      await loadData();
      setUploadStatus(res?.hard_deleted ? "File deleted (removed everywhere)." : "Removed from your portal.");
      setTimeout(() => setUploadStatus(""), 2000);
    } catch (err) {
      if (err?.status === 401) {
        setError("Session expired. Please log in again.");
        navigate("/login", { replace: true });
        return;
      }
      setError(err.message || "Failed to delete file");
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

  const statusLabel = (s) => (s === "opened" ? "Opened" : "Pending");
  const statusClass = (s) => (s === "opened" ? "badge badge-opened" : "badge badge-pending");

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
            Send Transfer (multiple files)
          </h2>
          <form onSubmit={handleSendTransfer} className="send-form">
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
              <label htmlFor="accessCode" className="form-label">
                Access Code
              </label>
              <div className="transfer-code-row">
                <input
                  id="accessCode"
                  type="text"
                  value={accessCode}
                  onChange={(e) => setAccessCode(e.target.value)}
                  className="form-input"
                  placeholder="Enter code or generate"
                  autoComplete="off"
                />
                <button type="button" className="btn btn-secondary btn-sm" onClick={generateClientCode}>
                  <Sparkles size={16} />
                  Generate
                </button>
                <button type="button" className="btn btn-secondary btn-sm" onClick={copyCode} disabled={!accessCode}>
                  <Copy size={16} />
                  Copy
                </button>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="files" className="form-label">
                Files
              </label>
              <input
                id="files"
                type="file"
                multiple
                onChange={(e) => setSelectedFiles(Array.from(e.target.files || []))}
                className="form-input pretty-file"
                required
              />
              {selectedFiles.length > 0 && (
                <p className="mt-2 text-sm text-white/70">
                  Selected {selectedFiles.length} file(s)
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
                selectedFiles.length === 0 ||
                !(accessCode || "").trim() ||
                (accessCode || "").trim().length < 6
              }
            >
              <Upload className="inline mr-2" size={18} />
              Send Transfer
            </button>
          </form>
        </div>

        {/* Sent Transfers */}
        <div className="dashboard-section" id="sent-transfers-section">
          <h2 className="section-title">
            <Send className="inline mr-2" size={20} />
            Sent Transfers ({sentTransfers.length})
          </h2>
          {sentTransfers.length === 0 ? (
            <p className="text-white/50">No transfers sent yet.</p>
          ) : (
            <div className="files-list">
              {sentTransfers.map((t) => {
                const expanded = expandedTransferIds.has(t.transfer_id);
                const files = transferFiles[t.transfer_id] || [];
                return (
                  <div key={t.transfer_id} className="file-item transfer-item">
                    <File className="inline mr-2" size={18} />
                    <div className="file-info">
                      <p className="file-name">
                        Transfer #{t.transfer_id} <span className={statusClass(t.status)}>{statusLabel(t.status)}</span>
                      </p>
                      <p className="file-meta">
                        To: {t.receiver_email} • {t.file_count} file(s) • {formatDate(t.created_at)}
                      </p>
                      {expanded && files.length > 0 && (
                        <div className="transfer-files">
                          {files.map((f) => (
                            <div key={f.id} className="transfer-file-row">
                              <span className="transfer-file-name">{f.original_filename}</span>
                              <span className="transfer-file-meta">{formatFileSize(f.size_bytes)}</span>
                              <button
                                onClick={() => handleDownloadTransferFile(t.transfer_id, f.id, f.original_filename, false)}
                                className="btn btn-secondary btn-sm"
                              >
                                <Download size={16} />
                              </button>
                            </div>
                          ))}
                          <button
                            onClick={() => handleDownloadTransferZip(t.transfer_id, false)}
                            className="btn btn-secondary btn-sm"
                          >
                            Download all (zip)
                          </button>
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => toggleExpand(t.transfer_id, false, t.status)}
                      className="btn btn-secondary btn-sm"
                    >
                      {expanded ? (
                        <>
                          <EyeOff size={16} /> Hide
                        </>
                      ) : (
                        <>
                          <Eye size={16} /> View
                        </>
                      )}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Received Transfers */}
        <div className="dashboard-section" id="received-transfers-section" ref={receivedRef}>
          <h2 className="section-title">
            <Inbox className="inline mr-2" size={20} />
            Received Transfers ({receivedTransfers.length})
          </h2>
          {receivedTransfers.length === 0 ? (
            <p className="text-white/50">No transfers received yet.</p>
          ) : (
            <div className="files-list">
              {receivedTransfers.map((t) => {
                const expanded = expandedTransferIds.has(t.transfer_id);
                const files = transferFiles[t.transfer_id] || [];
                const isOpened = t.status === "opened";
                return (
                  <div key={t.transfer_id} className="file-item transfer-item">
                    <File className="inline mr-2" size={18} />
                    <div className="file-info">
                      <p className="file-name">
                        Transfer #{t.transfer_id} <span className={statusClass(t.status)}>{statusLabel(t.status)}</span>
                      </p>
                      <p className="file-meta">
                        From: {t.sender_email} • {t.file_count} file(s) • {formatDate(t.created_at)}
                      </p>
                      {expanded && isOpened && files.length > 0 && (
                        <div className="transfer-files">
                          {files.map((f) => (
                            <div key={f.id} className="transfer-file-row">
                              <span className="transfer-file-name">{f.original_filename}</span>
                              <span className="transfer-file-meta">{formatFileSize(f.size_bytes)}</span>
                              <button
                                onClick={() => handleDownloadTransferFile(t.transfer_id, f.id, f.original_filename, true)}
                                className="btn btn-secondary btn-sm icon-btn"
                              >
                                <Download size={16} />
                              </button>
                              <button
                                onClick={() => handleDeleteTransferFile(t.transfer_id, f.id, true)}
                                className="btn btn-secondary btn-sm icon-btn btn-danger"
                                title="Delete"
                              >
                                <Trash2 size={16} />
                              </button>
                            </div>
                          ))}
                          <button
                            onClick={() => handleDownloadTransferZip(t.transfer_id, true)}
                            className="btn btn-secondary btn-sm"
                          >
                            Download all (zip)
                          </button>
                        </div>
                      )}
                    </div>

                    {isOpened ? (
                      <button
                        onClick={() => toggleExpand(t.transfer_id, true, t.status)}
                        className="btn btn-secondary btn-sm"
                      >
                        {expanded ? (
                          <>
                            <EyeOff size={16} /> Hide
                          </>
                        ) : (
                          <>
                            <Eye size={16} /> View
                          </>
                        )}
                      </button>
                    ) : (
                      <button onClick={() => openVerifyModal(t.transfer_id)} className="btn btn-secondary btn-sm">
                        Enter code
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Incoming popup */}
      {showIncomingModal && incomingCount > 0 && (
        <div className="modal-overlay">
          <div className="modal">
            <h3 className="modal-title">New transfer received</h3>
            <p className="modal-text">
              Hey, you received {incomingCount} file transfer(s). Enter the code to open them.
            </p>
            <div className="modal-actions">
              <button
                className="btn btn-primary"
                type="button"
                onClick={() => {
                  setShowIncomingModal(false);
                  receivedRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
                }}
              >
                Open inbox
              </button>
              <button className="btn btn-secondary" type="button" onClick={() => setShowIncomingModal(false)}>
                Later
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Verify modal */}
      {verifyModal.open && (
        <div className="modal-overlay">
          <div className="modal">
            <h3 className="modal-title">Enter access code</h3>
            <p className="modal-text">This transfer is locked. Enter the code to view and download files.</p>
            <input
              className="form-input"
              type="text"
              value={verifyCode}
              onChange={(e) => setVerifyCode(e.target.value)}
              placeholder="Access code"
              autoComplete="off"
            />
            {verifyModal.error && <div className="alert alert-error"><p>{verifyModal.error}</p></div>}
            <div className="modal-actions">
              <button className="btn btn-primary" type="button" onClick={submitVerify} disabled={!verifyCode.trim()}>
                Verify
              </button>
              <button
                className="btn btn-secondary"
                type="button"
                onClick={() => setVerifyModal({ open: false, transferId: null, error: "" })}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
