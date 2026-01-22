// DEV ONLY — REMOVE WHEN BACKEND AUTH IS READY
// Temporary frontend-only authentication utilities for development

const DEV_TOKEN_KEY = "token";
const DEV_USER_KEY = "dev_user";

/**
 * DEV ONLY: Attempts to login with dev credentials
 * @param {string} email - Email (must be "user123@gmail.com" for dev mode)
 * @param {string} password - Password (must be "useruser" for dev mode)
 * @returns {boolean} - True if credentials match dev bypass
 */
export function loginDev(email, password) {
  if (email === "user123@gmail.com" && password === "useruser") {
    const devToken = "dev-token";
    const devUser = { email: "user123@gmail.com", role: "OWNER" };
    
    localStorage.setItem(DEV_TOKEN_KEY, devToken);
    localStorage.setItem(DEV_USER_KEY, JSON.stringify(devUser));
    localStorage.setItem("role", devUser.role);
    
    return true;
  }
  return false;
}

/**
 * DEV ONLY: Logs out by clearing all auth data
 */
export function logout() {
  localStorage.removeItem(DEV_TOKEN_KEY);
  localStorage.removeItem(DEV_USER_KEY);
  localStorage.removeItem("role");
}

/**
 * DEV ONLY: Gets current auth state
 * @returns {{token: string|null, user: object|null}} - Auth state
 */
export function getAuth() {
  const token = localStorage.getItem(DEV_TOKEN_KEY);
  const userStr = localStorage.getItem(DEV_USER_KEY);
  const user = userStr ? JSON.parse(userStr) : null;
  
  return { token, user };
}
