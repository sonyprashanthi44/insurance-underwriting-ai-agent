import { NavLink, Outlet } from "react-router-dom";

export default function Layout({ user, onLogout }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">UW</div>
          <div>
            <div className="brand-title">Underwriting AI</div>
            <div className="brand-sub">Decision Support</div>
          </div>
        </div>
        <nav>
          <NavLink end to="/">Queue & Insights</NavLink>
          <NavLink to="/applications/new">New Application</NavLink>
        </nav>
        <div className="sidebar-foot">
          <div className="user-chip">
            <strong>{user.full_name}</strong>
            <span>{user.role}</span>
          </div>
          <button className="btn ghost" onClick={onLogout}>Sign out</button>
        </div>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
