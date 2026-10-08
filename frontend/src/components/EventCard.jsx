import { Link } from "react-router-dom";
import { Clock, MapPin, Users } from "lucide-react";

const formatDate = (iso) =>
  new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });

export default function EventCard({ event, onRegister, registered = false, isDemo = false }) {
  // If it's a real API event, capacity and registered might have different names or need checking
  const capacity = event.capacity || 100;
  const registeredCount = event.registered || 0;
  const seatsLeft = capacity - registeredCount;
  const full = seatsLeft <= 0;
  
  // Real dates from backend
  const startIso = event.start_time || event.date;
  const eventDateStr = startIso ? (startIso.includes('T') ? startIso : `${startIso}T00:00:00`) : new Date().toISOString();
  const eventDate = new Date(eventDateStr);
  const fill = Math.min(100, Math.round((registeredCount / capacity) * 100));
  
  const formattedTime = event.start_time 
    ? new Date(event.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', hour12: true})
    : (event.time || 'TBA');

  return (
    <article className="event-card">
      <Link to={`/events/${event.id}`} style={{ display: 'contents', color: 'inherit' }}>
        <div className="event-card__banner">
          {event.poster_url ? (
            <img src={event.poster_url} alt={event.title} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', opacity: 0.8, zIndex: 0}} />
          ) : (
            <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(45deg, var(--brand-accent), #8b5cf6)', opacity: 0.2, zIndex: 0}} />
          )}
          <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', zIndex: 1, position: 'relative' }}>
            <span className="event-card__badge">{event.category}</span>
            <span className="event-card__badge" style={{ background: event.price === 0 || !event.price ? 'rgba(16, 185, 129, 0.9)' : 'rgba(0,0,0,0.6)' }}>
              {event.price === 0 || !event.price ? "Free" : `₹${event.price}`}
            </span>
          </div>
          <div style={{ zIndex: 1, position: 'relative', background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', padding: '0.5rem', borderRadius: 'var(--radius-md)', textAlign: 'center', minWidth: '56px', border: '1px solid rgba(255,255,255,0.1)' }}>
            <strong style={{ display: 'block', fontSize: '1.25rem', lineHeight: 1, color: '#fff' }}>{eventDate.toLocaleDateString("en-IN", { day: "2-digit" })}</strong>
            <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'rgba(255,255,255,0.8)', fontWeight: 600 }}>{eventDate.toLocaleDateString("en-IN", { month: "short" })}</span>
          </div>
        </div>

        <div className="event-card__content">
          <h3 className="event-card__title">{event.title}</h3>
          <ul className="event-card__meta">
            <li className="event-card__meta-item">
              <Clock size={16} />
              {formatDate(eventDateStr)} · {formattedTime}
            </li>
            <li className="event-card__meta-item">
              <MapPin size={16} />
              {event.venue || 'TBA'}
            </li>
          </ul>

          <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Users size={12} /> {full ? "Event full" : `${seatsLeft} seats left`}</span>
              <span>{fill}%</span>
            </div>
            <div style={{ width: '100%', height: '4px', background: 'var(--bg-secondary)', borderRadius: '2px', overflow: 'hidden' }}>
              <div style={{ width: `${fill}%`, height: '100%', background: full ? 'var(--danger)' : 'var(--brand-accent)', borderRadius: '2px' }} />
            </div>
          </div>
        </div>
      </Link>

      <div className="event-card__footer">
        <div style={{display: 'flex', gap: '0.5rem', width: '100%', padding: '0 var(--space-5) var(--space-5)'}}>
          {onRegister ? (
            <button
              className="btn btn--primary btn--sm btn--block"
              disabled={full || registered}
              onClick={(e) => { e.preventDefault(); onRegister(event); }}
            >
              {registered ? "Registered ✓" : full ? "Full" : "Register Now"}
            </button>
          ) : (
            <Link to={`/events/${event.id}`} className="btn btn--secondary btn--sm btn--block">View Details</Link>
          )}
        </div>
      </div>
    </article>
  );
}
