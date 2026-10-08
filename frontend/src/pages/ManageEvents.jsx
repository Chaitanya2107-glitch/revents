import { useState, useEffect } from "react";
import EventForm from "../components/EventForm.jsx";
import { managerAPI, eventsAPI } from "../services/api.js";
import { formatDate } from "../data/dummyData.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function ManageEvents() {
  const { user } = useAuth();
  const [list, setList] = useState([]);
  const [editing, setEditing] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const loadEvents = async () => {
    setLoading(true);
    try {
      const data = await managerAPI.getEvents();
      setList(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadEvents(); }, []);

  const handleSave = async (data) => {
    try {
      // Parse local date/time into ISO UTC strings
      const start = new Date(`${data.date}T${data.time || '00:00'}:00`);
      // Default end time to 2 hours after start
      const end = new Date(start.getTime() + 2 * 60 * 60 * 1000);
      // Default deadline to 1 hour before start
      const deadline = new Date(start.getTime() - 60 * 60 * 1000);
      
      const payload = {
        title: data.title,
        description: data.description,
        category: data.category,
        venue: data.venue,
        capacity: data.capacity,
        price: data.price || 0,
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        registration_deadline: deadline.toISOString(),
        poster_url: data.poster_url || null,
      };

      if (data.id) {
        await eventsAPI.updateEvent(data.id, payload);
      } else {
        await eventsAPI.createEvent(payload);
      }
      setEditing(null);
      loadEvents();
    } catch (err) {
      alert("Save failed: " + err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this event?")) return;
    try {
      await eventsAPI.deleteEvent(id);
      setList(l => l.filter(e => e.id !== id));
    } catch (err) {
      alert("Delete failed: " + err.message);
    }
  };

  const handlePublish = async (id) => {
    try {
      await eventsAPI.publishEvent(id);
      loadEvents();
    } catch (err) {
      alert("Publish failed: " + err.message);
    }
  };

  return (
    <div className="container page animate-fade-up">
      <header className="page__header" style={{ marginBottom: 'var(--space-6)' }}>
        <div>
          <h1>Manage Events</h1>
          <p className="muted">
            {user.role === "admin" ? "System-wide event administration." : "Create and manage your events."}
          </p>
        </div>
        {!editing && (
          <button className="btn btn--primary" onClick={() => setEditing("new")}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{marginRight: '8px'}}><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            Create Event
          </button>
        )}
      </header>

      {editing ? (
        <div className="card animate-fade-up">
          <h2 style={{ marginBottom: 'var(--space-5)' }}>{editing === "new" ? "Create New Event" : "Edit Event"}</h2>
          <EventForm
            initialValues={editing === "new" ? undefined : editing}
            onSubmit={handleSave}
            onCancel={() => setEditing(null)}
          />
        </div>
      ) : loading ? (
        <div className="center muted">Loading events...</div>
      ) : list.length === 0 ? (
        <div className="empty">
          <h3>No events found</h3>
          <p>You haven't created any events yet.</p>
        </div>
      ) : (
        <div className="table-wrap card">
          <table className="table">
            <thead>
              <tr>
                <th>Event Details</th>
                <th>Category</th>
                <th>Registrations</th>
                <th>Status</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {list.map((e) => (
                <tr key={e.id}>
                  <td data-label="Event Details">
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <strong style={{ fontSize: '1.05rem', color: 'var(--text)' }}>{e.title}</strong>
                      <span className="muted small">
                        {e.start_time ? new Date(e.start_time).toLocaleDateString() : 'TBA'} at {e.start_time ? new Date(e.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', hour12: true}) : 'TBA'}
                      </span>
                    </div>
                  </td>
                  <td data-label="Category"><span className="badge badge--primary">{e.category}</span></td>
                  <td data-label="Registrations">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div className="progress" style={{ width: '60px', height: '6px', margin: 0 }}><div className="progress__bar" style={{ width: `${((e.registered_count || 0) / (e.capacity || 100)) * 100}%` }} /></div>
                      <span className="tabular">{e.registered_count || 0}/{e.capacity || 100}</span>
                    </div>
                  </td>
                  <td data-label="Status">
                    <span className={`badge ${e.status === 'PUBLISHED' ? 'badge--success' : 'badge--secondary'}`}>
                      {e.status || 'DRAFT'}
                    </span>
                  </td>
                  <td data-label="Actions" className="table__actions">
                    {(!e.status || e.status === 'DRAFT') && (
                      <button className="btn btn--primary btn--sm" onClick={() => handlePublish(e.id)}>Publish</button>
                    )}
                    <button className="btn btn--secondary btn--sm" onClick={() => {
                      let dateStr = "", timeStr = "";
                      if (e.start_time) {
                        const d = new Date(e.start_time);
                        const pad = n => n.toString().padStart(2, '0');
                        dateStr = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
                        timeStr = `${pad(d.getHours())}:${pad(d.getMinutes())}`;
                      }
                      setEditing({ ...e, date: dateStr, time: timeStr });
                    }}>Edit</button>
                    <button className="btn btn--danger btn--sm" onClick={() => handleDelete(e.id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
