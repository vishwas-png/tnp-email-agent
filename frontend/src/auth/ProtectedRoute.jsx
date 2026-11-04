import { Navigate } from "react-router-dom";
import { useAuth } from "./context";

function ProtectedRoute({ children }) {
  const { status, retry } = useAuth();

  if (status === "loading") {
    return <p className="page-message">Loading…</p>;
  }
  if (status === "error") {
    return (
      <div className="page-message">
        <p>Can't reach the server.</p>
        <button onClick={retry}>Try again</button>
      </div>
    );
  }
  if (status === "out") {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default ProtectedRoute;
