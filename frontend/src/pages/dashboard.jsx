import { useEffect, useState } from "react";
import { AuthError, apiFetch } from "../api";
import NoticeCard from "./NoticeCard";
import "./Dashboard.css";

function Dashboard() {
  const [notices, setNotices] = useState(null);
  const [error, setError] = useState(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    apiFetch("/notices")
      .then((data) => {
        setNotices(data);
        setError(null);
      })
      .catch((e) => {
        // AuthError: the auth context already sends the user to login.
        if (!(e instanceof AuthError)) setError("Could not load notices.");
      });
  }, [attempt]);

  function retry() {
    setError(null);
    setAttempt((n) => n + 1);
  }

  return (
    <div>
      <h1>Dashboard</h1>
      {error && (
        <div className="page-message">
          <p className="error-text">{error}</p>
          <button onClick={retry}>Try again</button>
        </div>
      )}
      {!error && notices === null && <p className="page-message">Loading notices…</p>}
      {notices?.length === 0 && <p className="page-message">No notices yet.</p>}
      <div className="notice-grid">
        {notices?.map((notice) => (
          <NoticeCard key={notice.gmail_message_id} notice={notice} />
        ))}
      </div>
    </div>
  );
}

export default Dashboard;
