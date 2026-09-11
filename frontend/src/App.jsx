import {BrowserRouter , Routes , Route} from "react-router-dom"
import HomePage from "./pages/homepage";
import Dashboard from "./pages/dashboard";
import Chatbot from "./pages/chatbot";


function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/chatbot" element={<Chatbot />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;