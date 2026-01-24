import { useLocation } from "react-router-dom";
import AuthPage from "./AuthPage";

function Login({ onAuth }) {
  const location = useLocation();
  const registrationSuccess = location.state?.registrationSuccess || false;
  const registeredEmail = location.state?.registeredEmail || null;
  
  return <AuthPage initialMode="login" onAuth={onAuth} registrationSuccess={registrationSuccess} registeredEmail={registeredEmail} />;
}

export default Login;
