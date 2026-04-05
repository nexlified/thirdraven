import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { label: "Dashboard", icon: "◈", path: "/dashboard" },
  { label: "People", icon: "◎", path: "/people" },
  { label: "Organizations", icon: "⬡", path: "/organizations" },
  { label: "Events", icon: "◷", path: "/events" },
  { label: "Tasks", icon: "◫", path: "/tasks" },
  { label: "Notes", icon: "○", path: "/notes" },
  { label: "Transactions", icon: "₹", path: "/transactions" },
  { label: "Finances", icon: "◈", path: "/finances" },
  { label: "Budgets", icon: "⊟", path: "/budgets" },
  { label: "Subscriptions", icon: "◉", path: "/subscriptions" },
  { label: "Loans", icon: "◎", path: "/loans" },
  { label: "Reminders", icon: "◷", path: "/reminders" },
  { label: "Assets", icon: "◈", path: "/assets" },
  { label: "Vocabulary", icon: "◧", path: "/vocabulary" },
  { label: "Settings", icon: "⚙", path: "/settings" },
];

interface AppLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
  headerRight?: React.ReactNode;
}

export function AppLayout({ children, title, subtitle, headerRight }: AppLayoutProps) {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  function handleSignOut() {
    signOut();
    navigate("/login");
  }

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-icon">◈</span>
          <span className="brand-name">ThirdRaven</span>
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.label}
              to={item.path}
              className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="avatar">{user?.username[0].toUpperCase()}</div>
            <div className="user-details">
              <span className="user-name">{user?.username}</span>
              <span className="user-email">{user?.email}</span>
            </div>
          </div>
          <button className="btn-ghost" onClick={handleSignOut}>
            Sign out
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="page-header">
          <div>
            <h2>{title}</h2>
            {subtitle && <p className="page-subtitle">{subtitle}</p>}
          </div>
          {headerRight && <div className="page-header-right">{headerRight}</div>}
        </header>

        {children}
      </main>
    </div>
  );
}
