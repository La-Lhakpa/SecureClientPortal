import AuthPage from "./AuthPage";

function Register() {
  // Register does NOT call onAuth - user must login separately
  return <AuthPage initialMode="register" />;
}

export default Register;
