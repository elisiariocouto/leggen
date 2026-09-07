/**
 * The stored session token.
 *
 * Kept out of AuthContext because the router's `beforeLoad` guard runs
 * outside React and cannot read a hook, but must agree with the context on
 * whether there is a usable session.
 */
const TOKEN_KEY = "leggen_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

interface TokenPayload {
  sub?: string;
  exp?: number;
}

/** Decode a JWT payload without verifying it — the API is the authority. */
function decodePayload(token: string): TokenPayload | null {
  try {
    const base64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(atob(base64));
  } catch {
    return null;
  }
}

export function getTokenUsername(token: string): string | null {
  return decodePayload(token)?.sub ?? null;
}

/**
 * Whether a token is present and has not expired.
 *
 * A token without an `exp` claim is treated as usable — the API rejects it
 * if it disagrees, and the 401 interceptor clears it. This only avoids
 * showing the app to someone whose session has demonstrably lapsed.
 */
export function hasValidSession(): boolean {
  const token = getToken();
  if (!token) return false;
  const exp = decodePayload(token)?.exp;
  if (typeof exp !== "number") return true;
  return exp * 1000 > Date.now();
}

/**
 * Why the session ended, stashed for the login page to explain.
 *
 * sessionStorage rather than a router param: the 401 interceptor navigates
 * with a full page load, so React state does not survive the trip, and the
 * reason is per-tab and disposable.
 */
const LOGOUT_REASON_KEY = "leggen_logout_reason";

export type LogoutReason = "expired" | "invalid";

export function setLogoutReason(reason: LogoutReason): void {
  try {
    sessionStorage.setItem(LOGOUT_REASON_KEY, reason);
  } catch {
    // Storage can be unavailable (private mode, blocked cookies); the login
    // page simply falls back to its default message.
  }
}

/** Read and clear the reason, so it is shown once. */
export function takeLogoutReason(): LogoutReason | null {
  try {
    const reason = sessionStorage.getItem(LOGOUT_REASON_KEY);
    sessionStorage.removeItem(LOGOUT_REASON_KEY);
    return reason === "expired" || reason === "invalid" ? reason : null;
  } catch {
    return null;
  }
}
