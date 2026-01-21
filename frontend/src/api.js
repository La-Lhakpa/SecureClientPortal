const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

let authToken = null;

export function setToken(token) {
  authToken = token;
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
  const headers = {
    "Content-Type": "application/json",
    ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
    ...options.headers,
  };
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    clearToken();
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Request failed");
  }
  const contentType = res.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    return res.json();
  }
  return res;
}

export const apiClient = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: "POST", body: JSON.stringify(body) }),
  upload: (path, file) =>
    fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
      body: file,
    }).then(async (res) => {
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Upload failed");
      }
      return res.json();
    }),
  download: async (path) => {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
    });
    if (!res.ok) throw new Error("Download failed");
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    return url;
  },
};
