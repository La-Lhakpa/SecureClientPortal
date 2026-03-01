import { Link } from "react-router-dom";
import HeroBanner from "./HeroBanner";

function NavBar({ user, onLogout }) {
  return (
    <header className="nav">
      <div className="nav-left">
        <HeroBanner />
        {user && (
          <nav className="nav-links">
            {user.role === "OWNER" ? <Link to="/send">Owner</Link> : <Link to="/client">Client</Link>}
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