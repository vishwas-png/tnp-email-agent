import { Link, Outlet } from "react-router-dom";
import { useAuth } from "../auth/context";
import "./layout.css";

function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <>
      <header className="app-header">
        <nav>
          <Link to="/">Home</Link>
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/chatbot">Chatbot</Link>
        </nav>
        <div className="app-header-user">
          <span>{user.email}</span>
          <button onClick={logout}>Log out</button>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
    </>
  );
}

export default AppLayout;
