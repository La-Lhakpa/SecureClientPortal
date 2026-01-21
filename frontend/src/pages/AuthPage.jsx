import SecurityBackground from "../components/SecurityBackground";
import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  CheckCircle2,
  Chrome,
  Eye,
  EyeOff,
  Github,
  Loader2,
  Lock,
  Mail,
  ShieldCheck,
} from "lucide-react";
import { apiClient, saveToken, setToken } from "../api";

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function AuthPage({ initialMode = "login", onAuth }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [mode, setMode] = useState(initialMode);
  const [values, setValues] = useState({
    email: "",
    password: "",
    role: "CLIENT",
    remember: true,
  });
  const [touched, setTouched] = useState({});
  const [formError, setFormError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [success, setSuccess] = useState(false);
  const [rippleKey, setRippleKey] = useState(0);
  const [errorKey, setErrorKey] = useState(0);

  useEffect(() => {
    const nextMode = location.pathname.includes("register") ? "register" : "login";
    setMode(nextMode);
  }, [location.pathname]);

  useEffect(() => {
    setFormError("");
    setTouched({});
    setSuccess(false);
  }, [mode]);

  const validate = (nextValues) => {
    const nextErrors = {};
    if (!nextValues.email) nextErrors.email = "Email is required.";
    else if (!EMAIL_REGEX.test(nextValues.email)) nextErrors.email = "Enter a valid email.";
    if (!nextValues.password) nextErrors.password = "Password is required.";
    else if (nextValues.password.length < 8) nextErrors.password = "Use at least 8 characters.";
    if (mode === "register" && !nextValues.role) nextErrors.role = "Select a role.";
    return nextErrors;
  };

  const fieldErrors = useMemo(() => validate(values), [values, mode]);

  const handleChange = (field) => (event) => {
    const value = field === "remember" ? event.target.checked : event.target.value;
    setValues((prev) => ({ ...prev, [field]: value }));
  };

  const handleBlur = (field) => () => {
    setTouched((prev) => ({ ...prev, [field]: true }));
  };

  const handleModeSwitch = (nextMode) => {
    if (nextMode === mode) return;
    navigate(nextMode === "register" ? "/register" : "/login");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const nextErrors = validate(values);
    setFormError("");
    setTouched({ email: true, password: true, role: true });
    if (Object.keys(nextErrors).length > 0) {
      setErrorKey((prev) => prev + 1);
      return;
    }

    setLoading(true);
    setFormError("");
    try {
      if (mode === "login") {
        const res = await apiClient.post("/auth/login", {
          email: values.email,
          password: values.password,
        });
        saveToken(res.access_token);
        setToken(res.access_token);
        setSuccess(true);
        setTimeout(() => {
          setLoading(false);
          onAuth?.(res.access_token);
        }, 900);
      } else {
        await apiClient.post("/auth/register", {
          email: values.email,
          password: values.password,
          role: values.role,
        });
        setSuccess(true);
        setTimeout(() => {
          setLoading(false);
          navigate("/login");
        }, 900);
      }
    } catch (err) {
      setLoading(false);
      setSuccess(false);
      setFormError(err.message || "Something went wrong. Try again.");
      setErrorKey((prev) => prev + 1);
    }
  };

  const submitLabel = useMemo(() => {
    if (loading) return mode === "login" ? "Signing in..." : "Creating account...";
    if (success) return "Success";
    return mode === "login" ? "Login" : "Create account";
  }, [loading, success, mode]);

  return (
    <div className="min-h-screen bg-slate-950 text-white overflow-hidden animate-fade-in">
      <SecurityBackground />
      <div className="absolute inset-0 bg-black/8" />
      <div className="relative min-h-screen grid lg:grid-cols-[1.1fr_1fr]">
        <div className="relative hidden lg:flex flex-col justify-between px-16 py-16">
          {/* <div className="absolute inset-0 auth-gradient opacity-90" />
          <div className="absolute inset-0 bg-black/25" /> */}

          <div className="relative z-10 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/15 border border-white/30 shadow-lg animate-logo">
              <ShieldCheck className="h-6 w-6 text-white" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-white/60">Secure Client Portal</p>
              <h1 className="text-3xl font-semibold">Protect what matters</h1>
            </div>
          </div>
          <div className="relative z-10 max-w-md space-y-6">
            <p className="text-2xl font-italic leading-tight">
              Premium, encrypted collaboration for your most trusted client relationships.
            </p>
            <p className="text-white/90">
              Experience seamless access, powerful controls, and a calm interface designed for focus.
            </p>
            <div className="flex items-center gap-4 text-sm text-white/70">
              <div className="rounded-full bg-white/15 px-4 py-1.5">Enterprise grade</div>
              <div className="rounded-full bg-white/15 px-4 py-1.5">Zero-trust ready</div>
            </div>
          </div>

          <div className="relative z-10 flex gap-3">
            <div className="h-14 w-14 rounded-2xl border border-white/25 bg-white/10" />
            <div className="h-14 w-24 rounded-2xl border border-white/25 bg-white/10" />
            <div className="h-14 w-20 rounded-2xl border border-white/25 bg-white/10" />
          </div>

          <div className="floating delay-1 top-20 left-20 h-20 w-20 rounded-3xl border border-white/30 bg-white/10" />
          <div className="floating delay-2 bottom-24 left-36 h-12 w-12 rounded-full border border-white/20 bg-white/10" />
          <div className="floating delay-3 top-44 right-20 h-16 w-16 rotate-12 rounded-2xl border border-white/30 bg-white/10" />
        </div>

        <div className="relative flex items-center justify-center px-6 py-12">
          <div className="absolute -top-24 -right-12 h-48 w-48 rounded-full bg-indigo-500/30 blur-3xl" />
          <div className="absolute -bottom-24 -left-10 h-48 w-48 rounded-full bg-sky-500/30 blur-3xl" />

          <div className="relative w-full max-w-md rounded-3xl border border-white/20 bg-white/10 p-8 shadow-2xl backdrop-blur-xl animate-slide-up">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm uppercase tracking-[0.3em] text-white/60">Welcome</p>
                <h2 className="text-2xl font-semibold">{mode === "login" ? "Sign in" : "Create account"}</h2>
                <p className="mt-1 text-sm text-white/70">
                  {mode === "login" ? "Access your secure workspace." : "Join Secure Client Portal today."}
                </p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/15 border border-white/25 animate-logo">
                <ShieldCheck className="h-5 w-5 text-white" />
              </div>
            </div>

            <div className="mt-6 flex items-center rounded-full bg-white/10 p-1 text-sm">
              <button
                type="button"
                onClick={() => handleModeSwitch("login")}
                className={`flex-1 rounded-full px-4 py-2 font-medium transition ${
                  mode === "login" ? "bg-white text-slate-900 shadow-glow" : "text-white/70 hover:text-white"
                }`}
              >
                Login
              </button>
              <button
                type="button"
                onClick={() => handleModeSwitch("register")}
                className={`flex-1 rounded-full px-4 py-2 font-medium transition ${
                  mode === "register" ? "bg-white text-slate-900 shadow-glow" : "text-white/70 hover:text-white"
                }`}
              >
                Register
              </button>
            </div>

            <form onSubmit={handleSubmit} className="mt-6 space-y-4" key={mode}>
              <div className="space-y-4 animate-form">
                <div className="relative">
                  <div className="pointer-events-none absolute left-4 top-4 text-white/40">
                    <Mail className="h-4 w-4" />
                  </div>
                  <input
                    id="email"
                    type="email"
                    value={values.email}
                    onChange={handleChange("email")}
                    onBlur={handleBlur("email")}
                    placeholder=" "
                    autoComplete="email"
                    disabled={loading || success}
                    className="peer w-full rounded-2xl border border-white/20 bg-white/10 px-10 pb-3 pt-6 text-sm text-white outline-none transition focus:border-sky-300/70 focus:ring-2 focus:ring-sky-400/40"
                  />
                  <label
                    htmlFor="email"
                    className="absolute left-10 top-4 text-xs uppercase tracking-[0.2em] text-white/50 transition-all peer-placeholder-shown:top-5 peer-placeholder-shown:text-sm peer-placeholder-shown:tracking-normal peer-focus:top-4 peer-focus:text-xs peer-focus:tracking-[0.2em]"
                  >
                    Email 
                  </label>
                  {(touched.email || fieldErrors.email) && fieldErrors.email && (
                    <p className="mt-2 text-xs text-rose-200 animate-slide-shake">{fieldErrors.email}</p>
                  )}
                </div>

                <div className="relative">
                  <div className="pointer-events-none absolute left-4 top-4 text-white/40">
                    <Lock className="h-4 w-4" />
                  </div>
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    value={values.password}
                    onChange={handleChange("password")}
                    onBlur={handleBlur("password")}
                    placeholder=" "
                    autoComplete={mode === "login" ? "current-password" : "new-password"}
                    disabled={loading || success}
                    className="peer w-full rounded-2xl border border-white/20 bg-white/10 px-10 pb-3 pt-6 text-sm text-white outline-none transition focus:border-sky-300/70 focus:ring-2 focus:ring-sky-400/40"
                  />
                  <label
                    htmlFor="password"
                    className="absolute left-10 top-4 text-xs uppercase tracking-[0.2em] text-white/50 transition-all peer-placeholder-shown:top-5 peer-placeholder-shown:text-sm peer-placeholder-shown:tracking-normal peer-focus:top-4 peer-focus:text-xs peer-focus:tracking-[0.2em]"
                  >
                    Password
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowPassword((prev) => !prev)}
                    className="absolute right-4 top-4 text-white/60 transition hover:text-white"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    disabled={loading || success}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                  {(touched.password || fieldErrors.password) && fieldErrors.password && (
                    <p className="mt-2 text-xs text-rose-200 animate-slide-shake">{fieldErrors.password}</p>
                  )}
                </div>

                {mode === "register" && (
                  <div className="relative">
                    <select
                      id="role"
                      value={values.role}
                      onChange={handleChange("role")}
                      onBlur={handleBlur("role")}
                      disabled={loading || success}
                      className="w-full rounded-2xl border border-white/20 bg-white/10 px-4 pb-3 pt-5 text-sm text-white text-left outline-none transition focus:border-sky-300/70 focus:ring-2 focus:ring-sky-400/40"
                    >
                      <option className="text-slate-900 text-right" value="OWNER">
                        Owner
                      </option>
                      <option className="text-slate-900 text-right" value="CLIENT">
                        Client
                      </option>
                    </select>
                    <label htmlFor="role" className="absolute left-4 top-3 text-xs uppercase tracking-[0.2em] text-white/50">
                      Role
                    </label>
                    {(touched.role || fieldErrors.role) && fieldErrors.role && (
                      <p className="mt-2 text-xs text-rose-200 animate-slide-shake">{fieldErrors.role}</p>
                    )}
                  </div>
                )}

                {mode === "login" && (
                  <div className="flex items-center justify-between text-sm text-white/70">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={values.remember}
                        onChange={handleChange("remember")}
                        className="peer sr-only"
                      />
                      <span className="flex h-5 w-5 items-center justify-center rounded-md border border-white/30 bg-white/10 transition peer-checked:border-sky-300 peer-checked:bg-sky-400/30">
                        {values.remember && <span className="h-2.5 w-2.5 rounded-sm bg-sky-200" />}
                      </span>
                      Remember me
                    </label>
                    <a href="#" onClick={(event) => event.preventDefault()} className="text-white/70 transition hover:text-white">
                      Forgot password?
                    </a>
                  </div>
                )}

                {formError && (
                  <div key={errorKey} className="rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-xs text-rose-100 animate-slide-shake">
                    {formError}
                  </div>
                )}

                {success && (
                  <div className="flex items-center gap-2 rounded-2xl border border-emerald-400/30 bg-emerald-500/10 px-4 py-3 text-xs text-emerald-100">
                    <CheckCircle2 className="h-4 w-4 check-pop" />
                    {mode === "login" ? "Authenticated. Redirecting..." : "Account created. Redirecting..."}
                  </div>
                )}
              </div>

              <button
                type="submit"
                disabled={loading || success}
                onClick={() => setRippleKey((prev) => prev + 1)}
                className="relative flex w-full items-center justify-center gap-2 overflow-hidden rounded-2xl bg-white px-5 py-3 text-sm font-semibold text-slate-900 transition hover:-translate-y-0.5 hover:shadow-xl disabled:cursor-not-allowed disabled:bg-white/70"
              >
                <span key={rippleKey} className="ripple" />
                {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                <span>{submitLabel}</span>
              </button>
            </form>

            <div className="mt-6 space-y-4">
              <div className="flex items-center gap-3 text-xs text-white/50">
                <div className="h-px flex-1 bg-white/10" />
                <span>or continue with</span>
                <div className="h-px flex-1 bg-white/10" />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  className="flex items-center justify-center gap-2 rounded-2xl border border-white/20 bg-white/5 px-4 py-2 text-sm text-white/80 transition hover:border-white/40 hover:text-white"
                >
                  <Chrome className="h-4 w-4" />
                  Google
                </button>
                <button
                  type="button"
                  className="flex items-center justify-center gap-2 rounded-2xl border border-white/20 bg-white/5 px-4 py-2 text-sm text-white/80 transition hover:border-white/40 hover:text-white"
                >
                  <Github className="h-4 w-4" />
                  GitHub
                </button>
              </div>
            </div>

            <div className="mt-6 text-center text-sm text-white/60">
              {mode === "login" ? (
                <>
                  New here?{" "}
                  <button
                    type="button"
                    onClick={() => handleModeSwitch("register")}
                    className="font-semibold text-white transition hover:text-sky-200"
                  >
                    Create an account
                  </button>
                </>
              ) : (
                <>
                  Already have an account?{" "}
                  <button
                    type="button"
                    onClick={() => handleModeSwitch("login")}
                    className="font-semibold text-white transition hover:text-sky-200"
                  >
                    Login
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
  </div>
  );
}

export default AuthPage;

