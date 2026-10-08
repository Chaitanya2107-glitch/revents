import { useState, useEffect } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { eventsAPI, registrationsAPI } from "../services/api.js";
import { useAuth } from "../context/AuthContext.jsx";
import { formatDate } from "../data/dummyData.js";
import { ArrowLeft, CalendarDays, Clock, MapPin, Tag, Users } from "lucide-react";

export default function EventDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [event, setEvent] = useState(null);
  const [registered, setRegistered] = useState(false);
  const [loading, setLoading] = useState(true);
  const [registering, setRegistering] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadEvent() {
      try {
        const data = await eventsAPI.getEvent(id);
        setEvent(data);
        if (user && user.role === "student") {
          const regs = await registrationsAPI.getMyRegistrations();
          setRegistered(regs.some(r => String(r.event_id) === String(id) || String(r.eventId) === String(id)));
        }
      } catch (err) {
        setError("Event not found or failed to load.");
      } finally {
        setLoading(false);
      }
    }
    loadEvent();
  }, [id, user]);

  if (loading) return (
    <div className="container page empty animate-fade-in">
      <Clock size={32} className="text-muted" style={{ animation: 'spin 2s linear infinite' }} />
      <p>Loading event details...</p>
    </div>
  );

  if (error || !event) {
    return (
      <div className="container page empty animate-fade-in">
        <h3>{error}</h3>
        <Link to="/events" className="btn btn--primary">Back to events</Link>
      </div>
    );
  }

  const capacity = event.capacity || 100;
  const registeredCount = event.registered || 0;
  const seatsLeft = capacity - registeredCount;

  const handleRegister = async () => {
    if (!user) return navigate("/login");
    setRegistering(true);
    try {
      await eventsAPI.registerForEvent(event.id);
      setRegistered(true);
    } catch (err) {
      alert("Failed to register: " + err.message);
    } finally {
      setRegistering(false);
    }
  }

  return (
    <div className="container page animate-fade-in">
      <Link to="/events" className="muted small" style={{display: 'inline-flex', alignItems: 'center', gap: '4px', alignSelf: 'flex-start', padding: '4px 8px', borderRadius: '4px', background: 'var(--bg-secondary)', border: '1px solid var(--border)'}}>
        <ArrowLeft size={14} /> Back to events
      </Link>

      <div className="event-details-hero">
        {event.poster_url ? (
          <img src={event.poster_url} alt={event.title} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', opacity: 0.6, mixBlendMode: 'overlay', zIndex: 1}} />
        ) : (
          <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(45deg, var(--brand-accent), #8b5cf6)', opacity: 0.3, zIndex: 1}} />
        )}
        <div className="event-details-hero__content">
          <span className="badge" style={{marginBottom: 'var(--space-4)', background: 'rgba(255,255,255,0.15)', backdropFilter: 'blur(8px)', color: '#fff', border: '1px solid rgba(255,255,255,0.2)', padding: '4px 12px', fontSize: '0.875rem'}}>{event.category}</span>
          <h1>{event.title}</h1>
          <p style={{fontSize: '1.25rem', opacity: 0.9, fontWeight: 500}}>Organized by {event.organizer?.full_name || "the campus team"}</p>
        </div>
      </div>

      <div className="event-details-grid">
        <div className="stack">
          <section className="card animate-slide-up delay-1">
            <h3 style={{marginBottom: 'var(--space-4)', borderBottom: '1px solid var(--border)', paddingBottom: 'var(--space-3)'}}>About this event</h3>
            <p style={{whiteSpace: 'pre-wrap', lineHeight: '1.8', color: 'var(--text-secondary)'}}>{event.description}</p>
          </section>
        </div>

        <aside className="event-details-sidebar animate-slide-up delay-2">
          <div className="card">
            <div className="stack" style={{marginBottom: 'var(--space-6)'}}>
              <div className="meta-item">
                <CalendarDays />
                <div>
                  <small>Date</small>
                  <span>{event.start_time ? formatDate(event.start_time) : (event.date ? formatDate(event.date) : 'TBA')}</span>
                </div>
              </div>
              <div className="meta-item">
                <Clock />
                <div>
                  <small>Time</small>
                  <span>{event.start_time ? new Date(event.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', hour12: true}) : (event.time || 'TBA')}</span>
                </div>
              </div>
              <div className="meta-item">
                <MapPin />
                <div>
                  <small>Venue</small>
                  <span>{event.venue || 'TBA'}</span>
                </div>
              </div>
              <div className="meta-item">
                <Tag />
                <div>
                  <small>Price</small>
                  <span>{event.price === 0 || !event.price ? "Free Entry" : `₹${event.price}`}</span>
                </div>
              </div>
              <div className="meta-item">
                <Users />
                <div>
                  <small>Availability</small>
                  <span>{seatsLeft} / {capacity} seats left</span>
                </div>
              </div>
            </div>

            {(!user || user.role === "student") && (
              <button
                className="btn btn--primary btn--block btn--lg"
                disabled={registered || seatsLeft <= 0 || registering}
                onClick={handleRegister}
                style={{ 
                  background: registered ? 'var(--success)' : seatsLeft <= 0 ? 'var(--danger)' : 'var(--brand)',
                  borderColor: registered ? 'var(--success-border)' : seatsLeft <= 0 ? 'var(--danger-border)' : 'transparent',
                  color: registered || seatsLeft <= 0 ? 'white' : 'var(--bg)'
                }}
              >
                {registering ? "Registering..." : registered ? "Registered ✓" : seatsLeft <= 0 ? "Event Full" : user ? "Register Now" : "Log in to register"}
              </button>
            )}
            
            {user?.role === "organizer" && (
              <Link to="/manage-events" className="btn btn--secondary btn--block">Manage Event</Link>
            )}
            {user?.role === "admin" && (
              <div style={{display: 'flex', gap: 'var(--space-2)'}}>
                <button className="btn btn--secondary btn--block">Approve</button>
                <button className="btn btn--danger btn--block">Delete</button>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
