import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import QRTicket from "../components/QRTicket.jsx";
import { registrationsAPI, eventsAPI } from "../services/api.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function MyRegistrations() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [eventsMap, setEventsMap] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const regs = await registrationsAPI.getMyRegistrations();
        const allEvents = await eventsAPI.getEvents();
        const eMap = {};
        allEvents.forEach(e => eMap[e.id] = e);
        setEventsMap(eMap);
        setItems(regs);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const cancel = async (id) => {
    try {
      await registrationsAPI.cancelRegistration(id);
      setItems((list) => list.filter((r) => r.id !== id));
    } catch (err) {
      alert("Failed to cancel: " + err.message);
    }
  };

  return (
    <div className="container page animate-fade-up">
      <header className="page__header">
        <div>
          <h1>My Registrations</h1>
          <p className="muted">Your tickets and upcoming events.</p>
        </div>
      </header>

      {loading ? (
        <div className="center muted">Loading your tickets...</div>
      ) : items.length === 0 ? (
        <div className="empty animate-delay-1">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" style={{color: 'var(--primary-300)'}}><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
          <h3>You haven't registered for any events yet</h3>
          <p>Explore the campus catalog and claim your spot.</p>
          <Link to="/events" className="btn btn--primary">Browse events</Link>
        </div>
      ) : (
        <div className="stack">
          {items.map((reg, i) => {
            const eventId = reg.event_id || reg.eventId;
            const event = eventsMap[eventId];
            return (
              <div key={reg.id} className="reg-item" style={{ animationDelay: `${i * 0.1}s` }}>
                <QRTicket registration={reg} event={event} user={user} />
                <div style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'flex-end', marginTop: 'var(--space-4)', maxWidth: '800px', marginInline: 'auto' }}>
                  <Link to={`/events/${eventId}`} className="btn btn--secondary btn--sm">View event</Link>
                  <button className="btn btn--danger btn--sm" onClick={() => cancel(reg.id)}>
                    Cancel registration
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
