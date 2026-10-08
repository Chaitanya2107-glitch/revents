import { useMemo, useState, useEffect } from "react";
import EventCard from "../components/EventCard.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { eventsAPI, registrationsAPI } from "../services/api.js";
import { Search, Sparkles, FilterX } from "lucide-react";

const CATEGORIES = ["All", "Technical", "Cultural", "Sports", "Workshop", "Seminar"];

export default function Events() {
  const { user } = useAuth();
  const [events, setEvents] = useState([]);
  const [registeredIds, setRegisteredIds] = useState([]);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  useEffect(() => {
    Promise.all([
      eventsAPI.getEvents(),
      user ? registrationsAPI.getMyRegistrations() : Promise.resolve([])
    ])
      .then(([eventsData, regsData]) => {
        setEvents(eventsData || []);
        setRegisteredIds((regsData || []).map(r => r.event_id || r.eventId));
      })
      .catch(err => setError(err.message || "Failed to load events"))
      .finally(() => setLoading(false));
  }, [user]);

  const filtered = useMemo(
    () =>
      events.filter(
        (e) =>
          (category === "All" || e.category === category) &&
          (e.title || "").toLowerCase().includes(query.toLowerCase())
      ),
    [query, category, events]
  );

  const handleRegister = async (event) => {
    try {
      await eventsAPI.registerForEvent(event.id);
      setToast(`You're registered for “${event.title}”!`);
      setRegisteredIds(prev => [...prev, event.id]);
      setTimeout(() => setToast(""), 3000);
    } catch (err) {
      setToast(`Failed to register: ${err.message}`);
      setTimeout(() => setToast(""), 3000);
    }
  };

  return (
    <div className="container page events-page animate-fade-in">
      <header className="events-hero">
        <span className="events-hero__eyebrow"><Sparkles size={14} style={{ marginRight: '6px' }} /> Discover Campus Events</span>
        <h1>Experience <span className="text-gradient">Campus Life</span></h1>
        <p className="muted">Discover and register for technical, cultural, and sports events happening around you. Don't miss out on the best experiences.</p>
      </header>

      {toast && <div className="alert alert--success animate-fade-in" style={{ marginBottom: 'var(--space-6)' }} role="status">{toast}</div>}

      <section id="all-events" className="events-catalog animate-slide-up delay-1" aria-labelledby="all-events-heading">
        <div className="page__header" style={{ alignItems: 'flex-end' }}>
          <div>
            <h2 id="all-events-heading" style={{ fontSize: '1.5rem', marginBottom: '4px' }}>All Events</h2>
            <p className="muted small" role="status">
              Showing {filtered.length} {filtered.length === 1 ? "event" : "events"}
            </p>
          </div>
          <div style={{ position: 'relative', width: '100%', maxWidth: '320px' }}>
            <Search size={16} className="text-muted" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              style={{ paddingLeft: '36px' }}
              type="search"
              placeholder="Search events…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label="Search events"
            />
          </div>
        </div>

        <div className="chips" role="group" aria-label="Filter by category">
          {CATEGORIES.map((c) => (
            <button
              key={c}
              type="button"
              aria-pressed={category === c}
              className={`chip ${category === c ? "is-active" : ""}`}
              onClick={() => setCategory(c)}
            >
              {c}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="empty">
            <Sparkles size={32} className="text-muted" style={{ animation: 'spin 2s linear infinite' }} />
            <p>Loading catalog...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty">
            <FilterX size={32} className="text-muted" />
            <h3 style={{ margin: 0 }}>No events match your search</h3>
            <p className="muted" style={{ marginTop: '-12px' }}>Try a different keyword or explore another category.</p>
            <button className="btn btn--secondary" onClick={() => { setQuery(""); setCategory("All"); }}>
              Clear filters
            </button>
          </div>
        ) : (
          <div className="grid events-grid">
            {filtered.map((ev) => (
              <EventCard
                key={ev.id}
                event={ev}
                registered={registeredIds.includes(ev.id)}
                onRegister={user?.role === "student" ? handleRegister : undefined}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
