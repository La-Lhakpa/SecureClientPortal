import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiClient } from "../api";

function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("CLIENT");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    try {
      await apiClient.post("/auth/register", { email, password, role });
      setSuccess("Account created. Please login.");
      setTimeout(() => navigate("/login"), 800);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="card auth-card">
      <h2>Create account</h2>
      <p className="muted">Choose your role and start sharing</p>
      <form onSubmit={handleSubmit} className="form">
        <label>Email</label>
        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required />
        <label>Password</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <label>Role</label>
        <select value={role} onChange={(e) => setRole(e.target.value)}>
          <option value="OWNER">Owner</option>
          <option value="CLIENT">Client</option>
        </select>
        {error && <div className="error">{error}</div>}
        {success && <div className="success">{success}</div>}
        <button type="submit">Register</button>
      </form>
      <div className="muted">
        Already have an account? <Link to="/login">Login</Link>
      </div>
    </div>
  );
}

export default Register;
