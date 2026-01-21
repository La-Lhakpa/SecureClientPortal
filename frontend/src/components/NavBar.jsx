import { Link } from "react-router-dom";

function NavBar({ user, onLogout }) {
  return (
    <header className="nav">
      <div className="nav-left">
        <span className="brand">Secure File Sharing</span>
        {user && (
          <nav className="nav-links">
            {user.role === "OWNER" ? <Link to="/owner">Owner</Link> : <Link to="/client">Client</Link>}
          </nav>
        )}
      </div>
      <div className="nav-right">
        {user ? (
          <>
            <span className="pill">{user.email}</span>
            <button className="secondary" onClick={onLogout}>
              Logout
            </button>
          </>
        ) : (
          <Link to="/login">Login</Link>
        )}
      </div>
    </header>
  );
}

export default NavBar;
