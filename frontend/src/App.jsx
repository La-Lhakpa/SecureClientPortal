import { Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { apiClient, getStoredToken, clearToken, saveToken, setToken } from "./api";
import SecurityBackground from "./components/SecurityBackground";



// DEV ONLY — REMOVE WHEN BACKEND AUTH IS READY
import { getAuth, logout as logoutDev } from "./utils/auth";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Send from "./pages/Send";
import ClientDashboard from "./pages/ClientDashboard";
import NavBar from "./components/NavBar";

function ProtectedRoute({ children, role }) {
  const token = getStoredToken();
  if (!token) return <Navigate to="/login" replace />;
  // role gating is handled by server too; this is just UX
  const storedRole = localStorage.getItem("role");
  if (role && storedRole && storedRole !== role) return <Navigate to={storedRole === "OWNER" ? "/send" : "/client"} replace />;
  return children;
}

function App() {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();
  const isAuthRoute = location.pathname === "/login" || location.pathname === "/register";

  useEffect(() => {
    const token = getStoredToken();
    if (token) setToken(token);
    if (token) {
      // DEV ONLY — REMOVE WHEN BACKEND AUTH IS READY
      // Check if this is a dev token first
      const devAuth = getAuth();
      if (devAuth.token === "dev-token" && devAuth.user) {
        setUser(devAuth.user);
        localStorage.setItem("role", devAuth.user.role);
        return;
      }
      
      // Normal backend auth
      apiClient
        .get("/me")
        .then((res) => {
          setUser(res);
          localStorage.setItem("role", res.role);
        })
        .catch(() => clearToken());
    }
  }, []);

  const handleLogout = () => {
    // DEV ONLY — REMOVE WHEN BACKEND AUTH IS READY
    logoutDev();
    clearToken();
    setUser(null);
    navigate("/login");
  };

  const handleAuthSuccess = (token) => {
    saveToken(token);
    setToken(token);
    
    // DEV ONLY — REMOVE WHEN BACKEND AUTH IS READY
    // Check if this is a dev token
    if (token === "dev-token") {
      const devAuth = getAuth();
      if (devAuth.user) {
        setUser(devAuth.user);
        localStorage.setItem("role", devAuth.user.role);
        navigate("/send");
        return;
      }
    }
    
    // Normal backend auth
    apiClient.get("/me").then((res) => {
      setUser(res);
      localStorage.setItem("role", res.role);
      navigate(res.role === "OWNER" ? "/send" : "/client");
    });
  };

  return (
    <div className="app-shell">
      <div className="app-background">
        <SecurityBackground />
        <div className="app-overlay" />
      </div>
  
      <div className="app-content">
        {!isAuthRoute && <NavBar user={user} onLogout={handleLogout} />}
        <div className={isAuthRoute ? "" : "page"}>
          <Routes>
            <Route path="/login" element={<Login onAuth={handleAuthSuccess} />} />
            <Route path="/register" element={<Register />} />
            <Route
              path="/send"
              element={
                <ProtectedRoute role="OWNER">
                  <Send user={user} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/client"
              element={
                <ProtectedRoute>
                  <ClientDashboard user={user} />
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
