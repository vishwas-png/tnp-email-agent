import { useSyncExternalStore } from "react";

// The theme lives on <html class="dark">; index.html sets it before first paint.
// This tiny store lets every component that uses the hook see the same value.
const listeners = new Set();

function getTheme() {
  return document.documentElement.classList.contains("dark") ? "dark" : "light";
}

function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function toggle() {
  const next = getTheme() === "dark" ? "light" : "dark";
  document.documentElement.classList.toggle("dark", next === "dark");
  try {
    localStorage.setItem("theme", next);
  } catch {
    // storage blocked: the choice just won't be remembered
  }
  listeners.forEach((listener) => listener());
}

export function useTheme() {
  const theme = useSyncExternalStore(subscribe, getTheme);
  return { theme, toggle };
}
