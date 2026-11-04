import { BrowserRouter, Routes, Route } from "react-router-dom";
import AuthProvider from "./auth/AuthProvider";
import ProtectedRoute from "./auth/ProtectedRoute";
import AppLayout from "./components/AppLayout";
import LoginPage from "./pages/login";
import HomePage from "./pages/homepage";
import Dashboard from "./pages/dashboard";
import Chatbot from "./pages/chatbot";


function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
            <Route path="/" element={<HomePage />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/chatbot" element={<Chatbot />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
