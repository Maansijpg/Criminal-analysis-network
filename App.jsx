import { Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import CaseGraph from "./pages/CaseGraph";
import Alerts from "./pages/Alerts";
import AddSuspect from "./pages/AddSuspect";

function RequireAuth({ children }) {
  const officer = localStorage.getItem("officer");
  return officer ? children : <Navigate to="/login" replace />;
}

export default function App() {
  const officer = localStorage.getItem("officer");
  return (
    <>
      {officer && <Navbar />}
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
        <Route path="/case/:caseId" element={<RequireAuth><CaseGraph /></RequireAuth>} />
        <Route path="/alerts" element={<RequireAuth><Alerts /></RequireAuth>} />
        <Route path="/add-suspect" element={<RequireAuth><AddSuspect /></RequireAuth>} />
      </Routes>
    </>
  );
}