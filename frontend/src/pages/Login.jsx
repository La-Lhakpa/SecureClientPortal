import { useState } from "react";
import { Link } from "react-router-dom";
import { apiClient, saveToken, setToken } from "../api";

function Login({ onAuth }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await apiClient.post("/auth/login", { email, password });
      saveToken(res.access_token);
      setToken(res.access_token);
      onAuth(res.access_token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card auth-card">
      <h2>Welcome back</h2>
      <p className="muted">Sign in to continue</p>
      <form onSubmit={handleSubmit} className="form">
        <label>Email</label>
        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required />
        <label>Password</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        {error && <div className="error">{error}</div>}
        <button type="submit" disabled={loading}>
          {loading ? "Signing in..." : "Login"}
        </button>
      </form>
      <div className="muted">
        New here? <Link to="/register">Create an account</Link>
      </div>
    </div>
  );
}

export default Login;
