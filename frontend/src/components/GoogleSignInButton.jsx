import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient, setToken } from "../api";

function GoogleSignInButton({ onSuccess }) {
  const containerRef = useRef(null);
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    
    if (!clientId) {
      setError("Google login not configured. Please contact support.");
      return;
    }

    // Wait for Google Identity Services to load
    const checkGoogleLoaded = () => {
      if (window.google && window.google.accounts && window.google.accounts.id) {
        initializeGoogleSignIn(clientId);
      } else {
        setTimeout(checkGoogleLoaded, 100);
      }
    };

    // Start checking after a short delay
    setTimeout(checkGoogleLoaded, 100);

    return () => {
      // Cleanup if component unmounts
      if (containerRef.current) {
        containerRef.current.innerHTML = "";
      }
    };
  }, []);

  const initializeGoogleSignIn = (clientId) => {
    if (!containerRef.current) return;

    try {
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: handleCredentialResponse,
      });

      window.google.accounts.id.renderButton(containerRef.current, {
        theme: "outline",
        size: "large",
        width: 300,
        text: "signin_with",
        type: "standard",
      });
    } catch (err) {
      console.error("[GoogleSignIn] Initialization error:", err);
      setError("Failed to initialize Google Sign-In. Please refresh the page.");
    }
  };

  const handleCredentialResponse = async (response) => {
    if (!response.credential) {
      setError("No credential received from Google.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const result = await apiClient.post("/auth/google", {
        id_token: response.credential,
      });

      if (result.access_token) {
        setToken(result.access_token);
        console.log("[GoogleSignIn] Login successful, token stored");
        
        // Call onSuccess callback if provided (for App.jsx to set user state)
        if (onSuccess) {
          onSuccess(result.access_token);
        }
        
        // Navigate to dashboard
        navigate("/dashboard", { replace: true });
      } else {
        throw new Error("No access token received from server");
      }
    } catch (err) {
      console.error("[GoogleSignIn] Login error:", err);
      setError(err.message || "Google sign-in failed. Please try again.");
      setLoading(false);
    }
  };

  return (
    <div className="space-y-2">
      <div ref={containerRef} className="w-full"></div>
      {loading && (
        <p className="text-xs text-white/70 text-center">Signing in...</p>
      )}
      {error && (
        <div className="rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-xs text-rose-100">
          {error}
        </div>
      )}
    </div>
  );
}

export default GoogleSignInButton;
