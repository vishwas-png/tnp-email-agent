import { useEffect, useState } from "react";
import { API_URL, AuthError, apiFetch } from "../api";
import { AuthContext } from "./context";

function loadUser(setAuth) {
  return apiFetch("/me")
    .then((user) => setAuth({ status: "in", user }))
    .catch((error) => setAuth({ status: error instanceof AuthError ? "out" : "error", user: null }));
}

function AuthProvider({ children }) {
  const [auth, setAuth] = useState({ status: "loading", user: null });

  useEffect(() => {
    loadUser(setAuth);
    // apiFetch fires this when a refresh also fails, from any page.
    const onExpired = () => setAuth({ status: "out", user: null });
    window.addEventListener("auth:expired", onExpired);
    return () => window.removeEventListener("auth:expired", onExpired);
  }, []);

  function retry() {
    setAuth({ status: "loading", user: null });
    loadUser(setAuth);
  }

  async function logout() {
    try {
      await fetch(`${API_URL}/logout`, { method: "POST", credentials: "include" });
    } finally {
      setAuth({ status: "out", user: null });
    }
  }

  return <AuthContext.Provider value={{ ...auth, retry, logout }}>{children}</AuthContext.Provider>;
}

export default AuthProvider;
