// Authentication utilities - now using real backend

/**
 * Logs out by clearing all auth data
 */
export function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("role");
}
