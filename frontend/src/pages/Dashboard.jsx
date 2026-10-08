import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import QRScanner from "../components/QRScanner.jsx";
import { managerAPI, eventsAPI, registrationsAPI } from "../services/api.js";
import { formatDate } from "../data/dummyData.js";
import { Activity, Calendar, Ticket, ArrowRight, UserCheck, Settings, Users, Zap, CalendarDays } from "lucide-react";

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        if (user.role === "student") {
          const [regs, allEvents] = await Promise.all([
            registrationsAPI.getMyRegistrations(),
            eventsAPI.getEvents()
          ]);
          setStats([
            { label: "Registered Events", value: regs.length, icon: CalendarDays },
            { label: "Confirmed Tickets", value: regs.filter(r => r.status === "Confirmed").length, icon: Ticket }
          ]);
          setEvents((allEvents || []).slice(0, 4));
        } else {
          const dashData = await managerAPI.getDashboard();
          setStats([
            { label: "Total Events", value: dashData.total_events || 0, icon: Calendar },
            { label: "Total Registrations", value: dashData.total_registrations || 0, icon: Users }
          ]);
          const myEvents = await managerAPI.getEvents();
          setEvents((myEvents || []).slice(0, 4));
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [user]);

  const displayName = user.full_name || user.name || (user.email ? user.email.split('@')[0] : "User");

  return (
    <div className="container page animate-fade-in">
      <header className="dashboard-hero">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <div className="avatar" style={{ width: '40px', height: '40px', fontSize: '1.25rem' }}>
            {displayName[0].toUpperCase()}
          </div>
          <div>
            <h1 style={{ fontSize: '1.5rem', marginBottom: '2px' }}>Welcome back, {displayName}</h1>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className={`badge badge--${user.role}`}>{user.role}</span>
              <span className="muted small">Connected to Workspace</span>
            </div>
          </div>
        </div>
        <p className="muted" style={{ maxWidth: '600px', margin: '16px 0' }}>
          Here's an overview of your campus events and activities. Start discovering new opportunities or manage your upcoming schedule.
        </p>
        <div className="row">
          {user.role === "student" ? (
            <>
              <Link to="/events" className="btn btn--primary">
                <Zap size={16} /> Discover Events
              </Link>
              <Link to="/my-registrations" className="btn btn--secondary">
                View My Tickets
              </Link>
            </>
          ) : (
            <>
              <Link to="/manage-events" className="btn btn--primary">
                <Settings size={16} /> Manage Events
              </Link>
              <Link to="/events" className="btn btn--secondary">
                Preview Live Site
              </Link>
            </>
          )}
        </div>
      </header>

      {loading ? (
        <div className="empty animate-fade-in">
          <Activity size={32} className="text-muted" style={{ animation: 'spin 2s linear infinite' }} />
          <p>Loading your dashboard...</p>
        </div>
      ) : (
        <>
          <div className="stats animate-slide-up delay-1">
            {stats.map((s, i) => {
              const Icon = s.icon || Activity;
              return (
                <div key={i} className="stat-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div className="stat-card__icon"><Icon size={20} /></div>
                  </div>
                  <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <span className="stat-card__value">{s.value}</span>
                    <span className="stat-card__label">{s.label}</span>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="dash-grid animate-slide-up delay-2">
            <section className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', paddingBottom: '16px', borderBottom: '1px solid var(--border)' }}>
                <h3 style={{ margin: 0, padding: 0, border: 'none' }}>{user.role === "student" ? "Featured Events" : "Recent Events"}</h3>
                <Link to={user.role === "student" ? "/events" : "/manage-events"} className="btn btn--ghost btn--sm">
                  View all <ArrowRight size={14} />
                </Link>
              </div>
              
              {events.length === 0 ? (
                <div className="empty" style={{ padding: '32px' }}>
                  <Calendar size={24} className="text-muted" style={{ marginBottom: '8px' }} />
                  <p className="muted small">No events found.</p>
                </div>
              ) : (
                <ul className="list">
                  {events.map((e) => (
                    <li key={e.id}>
                      <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                        <div style={{ width: '48px', height: '48px', borderRadius: '8px', background: 'var(--bg-secondary)', border: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--brand-accent)' }}>
                          <Calendar size={20} />
                        </div>
                        <div>
                          <strong>{e.title}</strong>
                          <p className="muted small" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            {e.start_time ? formatDate(e.start_time) : (e.date ? formatDate(e.date) : 'TBA')} 
                            <span style={{ opacity: 0.5 }}>•</span> 
                            {e.start_time ? new Date(e.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', hour12: true}) : (e.time || 'TBA')}
                            <span style={{ opacity: 0.5 }}>•</span> 
                            {e.venue}
                          </p>
                        </div>
                      </div>
                      <Link to={`/events/${e.id}`} className="btn btn--secondary btn--sm">Details</Link>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <div className="stack">
              {user.role === "student" && (
                <section className="card">
                  <div style={{ marginBottom: '20px', paddingBottom: '16px', borderBottom: '1px solid var(--border)' }}>
                    <h3 style={{ margin: 0, padding: 0, border: 'none' }}>Quick Actions</h3>
                  </div>
                  <ul className="list">
                    <li>
                      <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                        <Ticket size={18} className="text-muted" />
                        <div>
                          <strong>My Tickets</strong>
                          <p className="muted small">View QR codes for check-in</p>
                        </div>
                      </div>
                      <Link to="/my-registrations" className="btn btn--ghost btn--sm"><ArrowRight size={16} /></Link>
                    </li>
                  </ul>
                </section>
              )}

              {user.role === "organizer" && (
                <section className="card" style={{ padding: 0, overflow: 'hidden' }}>
                  <div style={{ padding: '20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <UserCheck size={18} />
                    <h3 style={{ margin: 0, padding: 0, border: 'none' }}>QR Check-in</h3>
                  </div>
                  <div style={{ padding: '20px' }}>
                    <QRScanner />
                  </div>
                </section>
              )}

              {user.role === "admin" && (
                <section className="card">
                  <div style={{ marginBottom: '20px', paddingBottom: '16px', borderBottom: '1px solid var(--border)' }}>
                    <h3 style={{ margin: 0, padding: 0, border: 'none' }}>System Status</h3>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: 'var(--success)' }}></div>
                    <p className="muted small">All systems operational.</p>
                  </div>
                </section>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

