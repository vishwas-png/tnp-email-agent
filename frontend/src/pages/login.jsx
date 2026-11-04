import { Navigate, useSearchParams } from "react-router-dom";
import { API_URL } from "../api";
import { useAuth } from "../auth/context";
import "../components/layout.css";

const ERRORS = {
  denied: "Google login was cancelled.",
  state: "That login link expired or was already used. Please try again.",
};

function LoginPage() {
  const { status } = useAuth();
  const [params] = useSearchParams();
  const error = ERRORS[params.get("error")];

  if (status === "in") {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="page-message">
      <h1>TNP Email Agent</h1>
      <p>Reads placement-cell emails, pulls out deadlines and companies, and notifies you about new notices.</p>
      {error && <p className="error-text">{error}</p>}
      <a href={`${API_URL}/connect-gmail`}>
        <button>Continue with Google</button>
      </a>
      <p>
        <small>Asks for read-only Gmail access. Only emails from the TNP cell are read and stored.</small>
      </p>
    </div>
  );
}

export default LoginPage;
