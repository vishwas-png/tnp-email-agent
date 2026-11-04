import { BrowserRouter, Navigate, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import AuthProvider from "./auth/AuthProvider";
import ProtectedRoute from "./auth/ProtectedRoute";
import AppLayout from "./components/AppLayout";
import { useTheme } from "./hooks/use-theme";
import LoginPage from "./pages/login";
import HomePage from "./pages/homepage";
import Dashboard from "./pages/dashboard";
import Chatbot from "./pages/chatbot";


function App() {
  const { theme } = useTheme();

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
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster theme={theme} position="top-center" richColors closeButton />
    </AuthProvider>
  );
}

export default App;
