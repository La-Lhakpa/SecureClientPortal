// Single source of truth for API base URL
const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

let authToken = null;

// Load token from localStorage on startup
const storedToken = localStorage.getItem("token");
if (storedToken) {
  authToken = storedToken;
}

export function setToken(token) {
  authToken = token;
  if (token) {
    localStorage.setItem("token", token);
  } else {
    localStorage.removeItem("token");
  }
}

export function saveToken(token) {
  localStorage.setItem("token", token);
}

export function getStoredToken() {
  return localStorage.getItem("token");
}

export function clearToken() {
  localStorage.removeItem("token");
  authToken = null;
}

async function request(path, options = {}) {
  // Always check localStorage for token in case it was updated elsewhere
  const token = authToken || localStorage.getItem("token");
  if (token && !authToken) {
    authToken = token;
  }
  
  // Ensure absolute URL
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
  
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };
  
  // Remove Content-Type for FormData
  if (options.body instanceof FormData) {
    delete headers["Content-Type"];
  }
  
  // DEV: Log request details
  if (import.meta.env.DEV) {
    console.log(`[API] ${options.method || "GET"} ${url}`, {
      hasToken: !!token,
      tokenLength: token?.length || 0,
      hasAuthHeader: !!headers.Authorization
    });
  }
  
  try {
    const res = await fetch(url, { ...options, headers });
    if (res.status === 401) {
      console.warn("[API] Received 401, clearing token");
      clearToken();
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      // Use detail field from FastAPI error response, or fallback to message
      const errorMsg = err.detail || err.message || `Request failed: ${res.status} ${res.statusText}`;
      console.error(`[API] Error [${res.status}]:`, errorMsg, "URL:", url);
      const e = new Error(errorMsg);
      e.status = res.status;
      throw e;
    }
    const contentType = res.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return res.json();
    }
    return res;
  } catch (error) {
    if (error.name === "TypeError" && error.message.includes("fetch")) {
      console.error("[API] Network error - Backend may be down:", API_BASE);
      throw new Error(`Cannot reach backend at ${API_BASE}. Is the server running?`);
    }
    throw error;
  }
}

export const apiClient = {
  get: (path) => request(path),
  post: (path, body) => {
    const bodyData = body instanceof FormData ? body : JSON.stringify(body);
    return request(path, { method: "POST", body: bodyData });
  },
  sendFile: ({ receiverId, file, onProgress }) =>
    new Promise((resolve, reject) => {
      const token = authToken || localStorage.getItem("token");
      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${API_BASE}/files/send`);
      if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      xhr.upload.onprogress = (evt) => {
        if (evt.lengthComputable && onProgress) {
          onProgress(Math.round((evt.loaded / evt.total) * 100));
        }
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch {
            resolve();
          }
        } else {
          if (xhr.status === 401) {
            console.warn("[API] Received 401 on sendFile, clearing token");
            clearToken();
          }
          let errorMsg = "Send failed";
          try {
            errorMsg = xhr.responseText ? JSON.parse(xhr.responseText).detail : errorMsg;
          } catch {
            // ignore parse errors
          }
          const e = new Error(errorMsg);
          e.status = xhr.status;
          reject(e);
        }
      };
      xhr.onerror = () => reject(new Error(`Network error - cannot reach ${API_BASE}`));
      const form = new FormData();
      form.append("receiver_id", receiverId);
      form.append("file", file);
      xhr.send(form);
    }),
  download: async (path) => {
    const token = authToken || localStorage.getItem("token");
    const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
    const res = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error("Download failed");
    const blob = await res.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    return blobUrl;
  },
};
