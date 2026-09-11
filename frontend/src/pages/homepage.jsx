import { Link } from "react-router-dom";

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
    </div>
  );
}

export default HomePage;