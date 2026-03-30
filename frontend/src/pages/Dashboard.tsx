import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { AppLayout } from "../components/AppLayout";
import { listPersons } from "../api/persons";

export function Dashboard() {
  const { user } = useAuth();
  const [peopleCount, setPeopleCount] = useState<number | null>(null);

  useEffect(() => {
    listPersons({ skip: 0, limit: 1 })
      .then((res) => setPeopleCount(res.total))
      .catch(() => {});
  }, []);

  const memberSince = user
    ? new Date(user.created_at).toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
      })
    : "";

  const statCards = [
    { label: "People", value: peopleCount !== null ? String(peopleCount) : "—", icon: "◎" },
    { label: "Events", value: "—", icon: "◷" },
    { label: "Follow-ups", value: "—", icon: "◉" },
    { label: "Open Tasks", value: "—", icon: "◫" },
  ];

  return (
    <AppLayout
      title="Dashboard"
      subtitle={`Welcome back, ${user?.username}. Member since ${memberSince}.`}
    >
      <div className="stats-grid">
        {statCards.map((card) => (
          <div key={card.label} className="stat-card">
            <span className="stat-icon">{card.icon}</span>
            <div className="stat-body">
              <span className="stat-value">{card.value}</span>
              <span className="stat-label">{card.label}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="content-grid">
        <section className="panel">
          <h3>Recent Activity</h3>
          <div className="empty-state">
            <span className="empty-icon">◎</span>
            <p>No activity yet. Start by adding people to your network.</p>
          </div>
        </section>

        <section className="panel">
          <h3>Upcoming Follow-ups</h3>
          <div className="empty-state">
            <span className="empty-icon">◷</span>
            <p>No follow-ups scheduled. Stay on top of your relationships.</p>
          </div>
        </section>
      </div>
    </AppLayout>
  );
}
