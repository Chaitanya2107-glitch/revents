import { formatDate } from "../data/dummyData.js";
import { useEffect, useState } from "react";
import { registrationsAPI } from "../services/api.js";
import { Download, Calendar, MapPin, Ticket, ShieldCheck } from "lucide-react";

// Deterministic pseudo-random pattern from the ticket id.
const SIZE = 21;
function buildPattern(seed) {
  let h = 0;
  for (const ch of String(seed)) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  const cells = [];
  for (let r = 0; r < SIZE; r++) {
    for (let c = 0; c < SIZE; c++) {
      const inFinder = (r < 7 && c < 7) || (r < 7 && c >= SIZE - 7) || (r >= SIZE - 7 && c < 7);
      if (inFinder) {
        const rr = r >= SIZE - 7 ? r - (SIZE - 7) : r;
        const cc = c >= SIZE - 7 ? c - (SIZE - 7) : c;
        const edge = rr === 0 || rr === 6 || cc === 0 || cc === 6;
        const core = rr >= 2 && rr <= 4 && cc >= 2 && cc <= 4;
        cells.push(edge || core);
      } else {
        h = (h * 1664525 + 1013904223) >>> 0;
        cells.push((h >>> 16) % 2 === 0);
      }
    }
  }
  return cells;
}

export default function QRTicket({ registration, event, user }) {
  const [ticketData, setTicketData] = useState(null);

  useEffect(() => {
    // If backend provides a ticket endpoint, fetch it to get real QR string
    registrationsAPI.getTicket(registration.id).then(data => setTicketData(data)).catch(() => {});
  }, [registration.id]);

  const qrSeed = ticketData?.qr_code || ticketData?.ticket_code || `REG-${registration.id}`;
  const cells = buildPattern(qrSeed);
  const displayName = user?.full_name || user?.name || (user?.email ? user.email.split('@')[0] : 'Student');

  return (
    <div className="qr-ticket animate-scale-in delay-1">
      <div className="qr-ticket__design" style={{ backgroundImage: event?.poster_url ? `url(${event.poster_url})` : 'none' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Ticket size={24} color="#fff" />
            <h2 style={{ margin: 0 }}>Entry Pass</h2>
          </div>
          <span className="badge" style={{ background: 'var(--success)', color: '#fff', border: 'none' }}>
            {registration.status || 'Confirmed'} <ShieldCheck size={12} style={{ marginLeft: '4px', display: 'inline' }} />
          </span>
        </div>
        <div style={{ marginTop: 'auto' }}>
          <div style={{fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.1em', opacity: 0.8, marginBottom: '4px'}}>Ticket Holder</div>
          <div style={{fontSize: '1.25rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px'}}>
            <div className="avatar" style={{ background: '#fff', color: '#000', width: '28px', height: '28px' }}>{displayName[0].toUpperCase()}</div>
            {displayName}
          </div>
        </div>
      </div>
      
      <div className="qr-ticket__main">
        <div style={{flex: 1}}>
          <h3 style={{fontSize: '1.5rem', marginBottom: 'var(--space-5)', lineHeight: 1.2}}>{event?.title || 'Unknown Event'}</h3>
          
          <div className="qr-ticket__meta">
            <div>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Calendar size={12} /> Date & Time</span>
              <strong>{event?.start_time ? formatDate(event.start_time) : (event?.date ? formatDate(event.date) : 'TBA')} {event?.start_time ? new Date(event.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true }) : (event?.time || 'TBA')}</strong>
            </div>
            <div>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><MapPin size={12} /> Venue</span>
              <strong>{event?.venue || 'TBA'}</strong>
            </div>
          </div>
        </div>
        
        <div className="qr-ticket__code-wrap">
          <div>
            <div style={{fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase'}}>Scan for entry</div>
            <div style={{fontFamily: 'monospace', fontSize: '1.25rem', letterSpacing: '1px', fontWeight: 500, color: 'var(--text)', marginBottom: '16px'}}>{qrSeed}</div>
            <button className="btn btn--secondary btn--sm" onClick={() => {
              window.open(`${import.meta.env.VITE_API_URL || 'http://localhost:8001/api'}/registrations/${registration.id}/ticket/pdf`, '_blank')
            }}>
              <Download size={14} /> Download PDF
            </button>
          </div>
          
          <div
            className="qr-grid qr-code-img"
            role="img"
            aria-label="QR code"
            style={{ 
              gridTemplateColumns: `repeat(${SIZE}, 1fr)`, 
              display: 'grid', 
              gap: '0',
              imageRendering: 'pixelated'
            }}
          >
            {cells.map((on, i) => (
              <span key={i} style={{ background: on ? '#000' : '#fff', width: '100%', height: '100%' }} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
