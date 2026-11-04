import { postJson } from "./api";

const ASKED_KEY = "notificationsAsked";

function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  return Uint8Array.from([...rawData].map((char) => char.charCodeAt(0)));
}

export function notificationsSupported() {
  return "Notification" in window && "serviceWorker" in navigator && "PushManager" in window;
}

// "default" (not asked yet), "granted", "denied", or "unsupported"
export function getPermission() {
  return notificationsSupported() ? Notification.permission : "unsupported";
}

// Reuses this browser's existing subscription if there is one. The backend
// upserts by endpoint, so calling this on every visit is safe.
export async function subscribeAndSave() {
  const registration = await navigator.serviceWorker.ready;
  const subscription =
    (await registration.pushManager.getSubscription()) ||
    (await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(import.meta.env.VITE_VAPID_PUBLIC_KEY),
    }));

  const { endpoint, keys } = subscription.toJSON();
  await postJson("/save-subscription", { endpoint, p256dh: keys.p256dh, auth: keys.auth });
}

export async function enableNotifications() {
  const permission = await Notification.requestPermission();
  if (permission === "granted") {
    await subscribeAndSave();
  }
  return permission;
}

// Auto-prompt only once per browser, so we do not nag on every visit.
// localStorage can throw (private mode, blocked storage), so guard it.
export function alreadyAsked() {
  try {
    return localStorage.getItem(ASKED_KEY) === "1";
  } catch {
    return true;
  }
}

export function markAsked() {
  try {
    localStorage.setItem(ASKED_KEY, "1");
  } catch {
    // ignore: worst case we ask again next visit
  }
}
