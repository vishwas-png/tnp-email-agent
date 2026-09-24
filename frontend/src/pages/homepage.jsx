import { Link } from "react-router-dom";


function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  return Uint8Array.from([...rawData].map((char) => char.charCodeAt(0)));
}

async function subscribeToPush() {
  const permission = await Notification.requestPermission();
  if (permission !== "granted") {
    console.log("Notification permission not granted");
    return;
  }

  const registration = await navigator.serviceWorker.ready;

  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(import.meta.env.VITE_VAPID_PUBLIC_KEY)
  });

  function arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = "";
    bytes.forEach((b) => (binary += String.fromCharCode(b)));
    return window.btoa(binary);
  }

  await fetch("http://localhost:8000/save-subscription", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      endpoint: subscription.endpoint,
      p256dh: arrayBufferToBase64(subscription.getKey("p256dh")),
      auth: arrayBufferToBase64(subscription.getKey("auth")),
    }),
  });
}

function HomePage() {
  return (
    <div>
      <h1>Welcome back</h1>
      <Link to="/dashboard">
        <button>Dashboard</button>
      </Link>
      <Link to="/chatbot">
        <button>Talk with chatbot</button>
      </Link>
      <button onClick={subscribeToPush}>Enable Notifications</button>
    </div>
  );
}

export default HomePage;