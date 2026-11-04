import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { alreadyAsked, enableNotifications, getPermission, markAsked, subscribeAndSave } from "../push";

function NotificationBanner({ permission, onEnable, error }) {
  if (permission === "granted") {
    return error ? <div className="banner banner-warning">{error}</div> : null;
  }
  if (permission === "unsupported") {
    return <div className="banner">This browser does not support push notifications.</div>;
  }
  if (permission === "denied") {
    return (
      <div className="banner banner-warning">
        Notifications are blocked. Allow them in your browser's site settings (the icon left of the address bar), then reload.
      </div>
    );
  }
  return (
    <div className="banner">
      <span>Get a notification when a new TNP notice arrives.</span>
      <button onClick={onEnable}>Enable notifications</button>
      {error && <span className="error-text">{error}</span>}
    </div>
  );
}

function HomePage() {
  const [permission, setPermission] = useState(getPermission);
  const [error, setError] = useState(null);

  function enable() {
    setError(null);
    enableNotifications()
      .then(setPermission)
      .catch(() => setError("Could not turn on notifications. Please try again."));
  }

  useEffect(() => {
    const current = getPermission();
    if (current === "granted") {
      // Keep the backend's copy of this device's subscription in sync.
      subscribeAndSave().catch(() => setError("Could not register this device for notifications."));
    } else if (current === "default" && !alreadyAsked()) {
      // Ask once, right after the first login. Some browsers ignore prompts that are
      // not caused by a click; the banner button is the fallback.
      markAsked();
      enableNotifications()
        .then(setPermission)
        .catch(() => setPermission(getPermission()));
    }
  }, []);

  return (
    <div className="page-message">
      <h1>Welcome back</h1>
      <NotificationBanner permission={permission} onEnable={enable} error={error} />
      <Link to="/dashboard">
        <button>Dashboard</button>
      </Link>{" "}
      <Link to="/chatbot">
        <button>Talk with chatbot</button>
      </Link>
    </div>
  );
}

export default HomePage;
