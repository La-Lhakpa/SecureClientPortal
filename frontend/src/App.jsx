import { Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { apiClient, getStoredToken, clearToken, setToken } from "./api";
import SecurityBackground from "./components/SecurityBackground";
import { logout } from "./utils/auth";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import NavBar from "./components/NavBar";

function ProtectedRoute({ children }) {
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [isChecking, setIsChecking] = useState(true);
  const token = getStoredToken();
  
  useEffect(() => {
    if (!token) {
      console.log("[ProtectedRoute] No token found, redirecting to login");
      setIsChecking(false);
      setIsAuthorized(false);
      return;
    }
    
    console.log("[ProtectedRoute] Token found, verifying with /me endpoint");
    // Ensure apiClient has the token
    setToken(token);
    
    // Verify token by calling /me
    apiClient
      .get("/me")
      .then((userData) => {
        console.log("[ProtectedRoute] Token valid, user:", userData);
        setIsAuthorized(true);
        setIsChecking(false);
      })
      .catch((err) => {
        console.error("[ProtectedRoute] Token verification failed:", err);
        // Token invalid
        clearToken();
        logout();
        setIsAuthorized(false);
        setIsChecking(false);
      });
  }, [token]);
  
  if (isChecking) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto"></div>
          <p className="mt-4 text-white/70">Verifying authentication...</p>
        </div>
      </div>
    );
  }
  
  if (!isAuthorized) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
}

function App() {
  const [user, setUser] = useState(null);
  const [backendStatus, setBackendStatus] = useState("checking");
  const navigate = useNavigate();
  const location = useLocation();
  const isAuthRoute = location.pathname === "/login" || location.pathname === "/register";

  // Check backend connectivity
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
        const res = await fetch(`${API_BASE}/health`);
        if (res.ok) {
          setBackendStatus("online");
        } else {
          setBackendStatus("offline");
        }
      } catch (err) {
        setBackendStatus("offline");
      }
    };
    checkBackend();
    // Check every 30 seconds
    const interval = setInterval(checkBackend, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const token = getStoredToken();
    if (token) {
      console.log("[App] Found token on mount, validating...");
      setToken(token);
      // Validate token with backend
      apiClient
        .get("/me")
        .then((res) => {
          console.log("[App] Token valid, user loaded:", res);
          setUser(res);
        })
        .catch((err) => {
          console.error("[App] Token validation failed:", err);
          // Token invalid, clear it
          clearToken();
          logout();
          setUser(null);
        });
    } else {
      console.log("[App] No token found on mount");
    }
  }, []);

  const handleLogout = () => {
    logout();
    clearToken();
    setUser(null);
    navigate("/login");
  };

  const handleAuthSuccess = async (token) => {
    console.log("[AUTH] handleAuthSuccess called with token length:", token?.length || 0);
    
    // Store token first
    setToken(token);
    console.log("[AUTH] Token stored in localStorage and apiClient");
    
    // Verify token works by calling /me
    try {
      const userData = await apiClient.get("/me");
      console.log("[AUTH] /me call successful, user:", userData);
      setUser(userData);
      // Navigate to dashboard after successful auth
      navigate("/dashboard");
    } catch (err) {
      console.error("[AUTH] /me call failed:", err);
      // If /me fails, clear token and redirect to login
      clearToken();
      logout();
      setUser(null);
      navigate("/login", { state: { error: "Authentication failed. Please login again." } });
    }
  };

  return (
    <div className="app-shell">
      <div className="app-background">
        <SecurityBackground />
        <div className="app-overlay" />
      </div>
  
      <div className="app-content">
        {backendStatus === "offline" && (
          <div className="backend-warning">
            <p>⚠️ Backend not reachable at {import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"}. Is the server running?</p>
          </div>
        )}
        {/* DEV: Show auth state in development */}
        {import.meta.env.DEV && (
          <div style={{ position: "fixed", top: "60px", right: "10px", background: "rgba(0,0,0,0.8)", color: "white", padding: "8px", fontSize: "11px", zIndex: 9999, borderRadius: "4px" }}>
            <div>Token: {getStoredToken() ? `Present (${getStoredToken().length} chars)` : "Missing"}</div>
            <div>User: {user ? user.email : "Not loaded"}</div>
          </div>
        )}
        {!isAuthRoute && <NavBar user={user} onLogout={handleLogout} />}
        <div className={isAuthRoute ? "" : "page"}>
          <Routes>
            <Route path="/login" element={<Login onAuth={handleAuthSuccess} />} />
            <Route path="/register" element={<Register />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard user={user} />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}
export default App;
