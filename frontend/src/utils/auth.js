// Authentication utilities - now using real backend

/**
 * Logs out by clearing all auth data
 */
export function logout() {
  localStorage.removeItem("token");
  // Remove any transfer access tokens
  const prefix = "transfer_token:";
  const keysToRemove = [];
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i);
    if (k && k.startsWith(prefix)) keysToRemove.push(k);
  }
  keysToRemove.forEach((k) => localStorage.removeItem(k));
}
