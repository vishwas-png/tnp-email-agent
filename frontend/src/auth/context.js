import { createContext, useContext } from "react";

// status: "loading" (checking /me), "in", "out", or "error" (server unreachable)
export const AuthContext = createContext(null);

export function useAuth() {
  return useContext(AuthContext);
}
