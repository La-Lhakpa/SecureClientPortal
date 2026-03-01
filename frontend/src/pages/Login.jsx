import AuthPage from "./AuthPage";

function Login({ onAuth }) {
  return <AuthPage initialMode="login" onAuth={onAuth} />;
}

export default Login;
