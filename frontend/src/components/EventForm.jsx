import { useState } from "react";
import { Upload, X } from "lucide-react";
import { eventsAPI } from "../services/api";

const EMPTY = {
  title: "",
  category: "Technical",
  date: "",
  time: "",
  venue: "",
  capacity: 100,
  price: 0,
  description: "",
  poster_url: "",
};

const CATEGORIES = ["Technical", "Cultural", "Sports", "Workshop", "Seminar", "Other"];

// Used for both "Add event" (no initialValues) and "Edit event".
export default function EventForm({ initialValues, onSubmit, onCancel }) {
  const [form, setForm] = useState({ ...EMPTY, ...initialValues });
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  
  const isEdit = Boolean(initialValues?.id);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      setUploading(true);
      setError(null);
      // Ensure backend /events/poster actually returns the URL or path
      const res = await eventsAPI.uploadPoster(file);
      setForm((f) => ({ ...f, poster_url: res.poster_url || res.url }));
    } catch (err) {
      setError("Failed to upload poster. " + err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit?.({
      ...form,
      capacity: Number(form.capacity),
      price: Number(form.price),
    });
  };

  return (
    <form className="card" onSubmit={handleSubmit} style={{ padding: '2rem' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h3 style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--text-primary)' }}>
          {isEdit ? "Edit Event Details" : "Create New Event"}
        </h3>
        <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
          {isEdit ? "Update the information for your event." : "Fill in the details to publish a new event to the platform."}
        </p>
      </div>

      {error && (
        <div className="empty-state" style={{ padding: '1rem', color: '#ff4d4d', backgroundColor: 'rgba(255,77,77,0.1)', marginBottom: '1.5rem' }}>
          {error}
        </div>
      )}

      {/* Poster Upload Area */}
      <div style={{ marginBottom: '2rem' }}>
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-secondary)' }}>Event Poster</label>
        <div 
          style={{ 
            border: '2px dashed var(--border-color)', 
            borderRadius: '12px', 
            padding: form.poster_url ? '0' : '3rem 2rem', 
            textAlign: 'center',
            position: 'relative',
            overflow: 'hidden',
            backgroundColor: 'var(--bg-tertiary)',
            transition: 'all 0.2s ease',
            cursor: 'pointer'
          }}
          onClick={() => !form.poster_url && document.getElementById('poster-upload').click()}
        >
          {form.poster_url ? (
            <div style={{ position: 'relative', width: '100%', height: '200px' }}>
              <img src={form.poster_url} alt="Poster preview" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              <button 
                type="button" 
                onClick={(e) => { e.stopPropagation(); setForm(f => ({ ...f, poster_url: '' })) }}
                style={{
                  position: 'absolute',
                  top: '1rem',
                  right: '1rem',
                  background: 'rgba(0,0,0,0.5)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '50%',
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  backdropFilter: 'blur(4px)'
                }}
              >
                <X size={16} />
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'var(--bg-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Upload size={20} color="var(--primary-color)" />
              </div>
              <div>
                <p style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{uploading ? 'Uploading...' : 'Click to upload poster'}</p>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>SVG, PNG, JPG or GIF (max. 5MB)</p>
              </div>
            </div>
          )}
          <input 
            id="poster-upload" 
            type="file" 
            accept="image/*" 
            style={{ display: 'none' }} 
            onChange={handleFileChange}
            disabled={uploading}
          />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        <div>
          <label htmlFor="title" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-secondary)' }}>Event Title</label>
          <input 
            id="title" 
            name="title" 
            value={form.title} 
            onChange={handleChange} 
            required 
            style={{ 
              width: '100%', 
              padding: '0.75rem 1rem', 
              borderRadius: '8px', 
              border: '1px solid var(--border-color)',
              background: 'var(--bg-secondary)',
              color: 'var(--text-primary)',
              fontSize: '1rem'
            }}
            placeholder="e.g., Annual Tech Symposium 2026"
          />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
        <div>
          <label htmlFor="category" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-secondary)' }}>Category</label>
          <select 
            id="category" 
            name="category" 
            value={form.category} 
            onChange={handleChange}
            style={{ 
              width: '100%', 
              padding: '0.75rem 1rem', 
              borderRadius: '8px', 
              border: '1px solid var(--border-color)',
              background: 'var(--bg-secondary)',
              color: 'var(--text-primary)',
              fontSize: '1rem',
              appearance: 'none'
            }}
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
        
        <div>
          <label htmlFor="venue" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-secondary)' }}>Venue</label>
          <input 
            id="venue" 
            name="venue" 
            value={form.venue} 
            onChange={handleChange} 
            required 
            style={{ 
              width: '100%', 
              padding: '0.75rem 1rem', 
              borderRadius: '8px', 
              border: '1px solid var(--border-color)',
              background: 'var(--bg-secondary)',
              color: 'var(--text-primary)',
              fontSize: '1rem'
            }}
            placeholder="e.g., Main Auditorium"
          />
        </div>
        
        <div>
          <label htmlFor="date" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-secondary)' }}>Date</label>
          <input 
            id="date" 
            type="date" 
            name="date" 
            value={form.date} 
            onChange={handleChange} 
            required 
            style={{ 
              width: '100%', 
              padding: '0.75rem 1rem', 
              borderRadius: '8px', 
              border: '1px solid var(--border-color)',
              background: 'var(--bg-secondary)',
              color: 'var(--text-primary)',
              fontSize: '1rem'
            }}
          />
        </div>
        
        <div>
          <label htmlFor="time" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-secondary)' }}>Time</label>
          <input 
            id="time" 
            type="time" 
            name="time" 
            value={form.time} 
            onChange={handleChange} 
            required 
            style={{ 
              width: '100%', 
              padding: '0.75rem 1rem', 
              borderRadius: '8px', 
              border: '1px solid var(--border-color)',
              background: 'var(--bg-secondary)',
              color: 'var(--text-primary)',
              fontSize: '1rem'
            }}
          />
        </div>
        
        <div>
          <label htmlFor="capacity" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-secondary)' }}>Capacity</label>
          <input 
            id="capacity" 
            type="number" 
            min="1" 
            name="capacity" 
            value={form.capacity} 
            onChange={handleChange} 
            style={{ 
              width: '100%', 
              padding: '0.75rem 1rem', 
              borderRadius: '8px', 
              border: '1px solid var(--border-color)',
              background: 'var(--bg-secondary)',
              color: 'var(--text-primary)',
              fontSize: '1rem'
            }}
          />
        </div>
        
        <div>
          <label htmlFor="price" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-secondary)' }}>Price (₹, 0 = free)</label>
          <input 
            id="price" 
            type="number" 
            min="0" 
            name="price" 
            value={form.price} 
            onChange={handleChange} 
            style={{ 
              width: '100%', 
              padding: '0.75rem 1rem', 
              borderRadius: '8px', 
              border: '1px solid var(--border-color)',
              background: 'var(--bg-secondary)',
              color: 'var(--text-primary)',
              fontSize: '1rem'
            }}
          />
        </div>
      </div>

      <div style={{ marginBottom: '2rem' }}>
        <label htmlFor="description" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-secondary)' }}>Description</label>
        <textarea
          id="description"
          name="description"
          rows="5"
          value={form.description}
          onChange={handleChange}
          required
          style={{ 
            width: '100%', 
            padding: '0.75rem 1rem', 
            borderRadius: '8px', 
            border: '1px solid var(--border-color)',
            background: 'var(--bg-secondary)',
            color: 'var(--text-primary)',
            fontSize: '1rem',
            resize: 'vertical',
            fontFamily: 'inherit'
          }}
          placeholder="Describe the event in detail..."
        />
      </div>

      <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', paddingTop: '1.5rem', borderTop: '1px solid var(--border-color)' }}>
        {onCancel && (
          <button type="button" className="btn btn-ghost" onClick={onCancel}>
            Cancel
          </button>
        )}
        <button type="submit" className="btn btn-primary" disabled={uploading}>
          {isEdit ? "Save Changes" : "Publish Event"}
        </button>
      </div>
    </form>
  );
}
