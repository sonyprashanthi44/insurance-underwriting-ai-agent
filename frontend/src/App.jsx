import { Navigate, Route, Routes } from "react-router-dom";
import { useEffect, useState } from "react";
import { me } from "./api/client";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import ApplicationDetail from "./pages/ApplicationDetail";
import NewApplication from "./pages/NewApplication";
import Layout from "./components/Layout";

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setLoading(false);
      return;
    }
    me()
      .then(setUser)
      .catch(() => localStorage.removeItem("token"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="center-screen">Loading workspace…</div>;

  return (
    <Routes>
      <Route
        path="/login"
        element={user ? <Navigate to="/" replace /> : <Login onLogin={setUser} />}
      />
      <Route
        path="/"
        element={user ? <Layout user={user} onLogout={() => { localStorage.removeItem("token"); setUser(null); }} /> : <Navigate to="/login" replace />}
      >
        <Route index element={<Dashboard />} />
        <Route path="applications/new" element={<NewApplication />} />
        <Route path="applications/:id" element={<ApplicationDetail />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
