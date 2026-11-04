export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export class AuthError extends Error {}

// Shared promise: if several requests get a 401 at once, they all wait for one refresh.
let refreshing = null;

function refreshSession() {
  if (!refreshing) {
    refreshing = fetch(`${API_URL}/refresh-token`, { method: "POST", credentials: "include" })
      .then((response) => response.ok)
      .catch(() => false)
      .finally(() => {
        refreshing = null;
      });
  }
  return refreshing;
}

// Every API call goes through here: sends cookies, refreshes once on 401, retries once.
// A second 401 means the session is really over, so the auth context shows the login page.
export async function apiFetch(path, options = {}) {
  const request = () => fetch(`${API_URL}${path}`, { ...options, credentials: "include" });

  let response = await request();
  if (response.status === 401 && (await refreshSession())) {
    response = await request();
  }
  if (response.status === 401) {
    window.dispatchEvent(new Event("auth:expired"));
    throw new AuthError("Not logged in");
  }
  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`);
  }
  return response.json();
}

export function postJson(path, body) {
  return apiFetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
