import { Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { apiClient, getStoredToken, clearToken, saveToken, setToken } from "./api";
import Login from "./pages/Login";
import Register from "./pages/Register";
import OwnerDashboard from "./pages/OwnerDashboard";
import ClientDashboard from "./pages/ClientDashboard";
import NavBar from "./components/NavBar";

function ProtectedRoute({ children }) {
  const token = getStoredToken();
  if (!token) return <Navigate to="/login" replace />;
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
      apiClient.get("/users/me").then((res) => setUser(res)).catch(() => clearToken());
    }
  }, []);

  const handleLogout = () => {
    clearToken();
    setUser(null);
    navigate("/login");
  };

  const handleAuthSuccess = (token) => {
    saveToken(token);
    setToken(token);
    apiClient.get("/users/me").then((res) => {
      setUser(res);
      navigate(res.role === "OWNER" ? "/owner" : "/client");
    });
  };

  return (
    <div className="app-shell">
      {!isAuthRoute && <NavBar user={user} onLogout={handleLogout} />}
      <div className={isAuthRoute ? "" : "page"}>
        <Routes>
          <Route path="/login" element={<Login onAuth={handleAuthSuccess} />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/owner"
            element={
              <ProtectedRoute>
                <OwnerDashboard user={user} />
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
  );
}

export default App;
