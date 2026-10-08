import { useState } from "react";
import { Camera, CheckCircle, XCircle } from "lucide-react";
import { managerAPI } from "../services/api";

export default function QRScanner({ onScan }) {
  const [scanning, setScanning] = useState(false);
  const [manual, setManual] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const report = async (code) => {
    if (!code) return;
    setLoading(true);
    setResult(null);
    try {
      // Actually verify the ticket via API
      const res = await managerAPI.verifyTicket({ qr_code: code });
      
      const payload = { 
        code, 
        success: true,
        message: res.message || "Successfully checked in!",
        time: new Date().toLocaleTimeString() 
      };
      
      setResult(payload);
      setScanning(false);
      onScan?.(payload);
    } catch (err) {
      setResult({
        code,
        success: false,
        message: err.message || "Invalid or already used ticket",
        time: new Date().toLocaleTimeString()
      });
    } finally {
      setLoading(false);
      setManual("");
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div 
        className={`scanner__viewfinder ${scanning ? "is-scanning" : ""}`}
        style={{
          position: 'relative',
          background: 'var(--bg-tertiary)',
          borderRadius: '16px',
          height: '240px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden',
          border: `2px dashed ${scanning ? 'var(--primary-color)' : 'var(--border-color)'}`,
          transition: 'all 0.3s ease'
        }}
      >
        <div style={{
          position: 'absolute', top: 16, left: 16, width: 24, height: 24, borderTop: '3px solid var(--primary-color)', borderLeft: '3px solid var(--primary-color)', borderRadius: '4px 0 0 0'
        }} />
        <div style={{
          position: 'absolute', top: 16, right: 16, width: 24, height: 24, borderTop: '3px solid var(--primary-color)', borderRight: '3px solid var(--primary-color)', borderRadius: '0 4px 0 0'
        }} />
        <div style={{
          position: 'absolute', bottom: 16, left: 16, width: 24, height: 24, borderBottom: '3px solid var(--primary-color)', borderLeft: '3px solid var(--primary-color)', borderRadius: '0 0 0 4px'
        }} />
        <div style={{
          position: 'absolute', bottom: 16, right: 16, width: 24, height: 24, borderBottom: '3px solid var(--primary-color)', borderRight: '3px solid var(--primary-color)', borderRadius: '0 0 4px 0'
        }} />
        
        {scanning && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '2px',
            background: 'var(--primary-color)',
            boxShadow: '0 0 12px 2px var(--primary-color)',
            animation: 'scan 2s infinite linear'
          }} />
        )}
        
        <div style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
          <Camera size={32} style={{ margin: '0 auto 0.5rem auto', opacity: scanning ? 1 : 0.5, color: scanning ? 'var(--primary-color)' : 'inherit' }} />
          <p style={{ fontWeight: 500 }}>
            {scanning ? "Scanning for QR codes..." : "Camera inactive"}
          </p>
        </div>
      </div>

      <style>
        {`
          @keyframes scan {
            0% { top: 10%; opacity: 0; }
            10% { opacity: 1; }
            90% { opacity: 1; }
            100% { top: 90%; opacity: 0; }
          }
        `}
      </style>

      <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
        {scanning ? (
          <>
            <button className="btn btn-ghost" onClick={() => setScanning(false)}>
              Stop Camera
            </button>
            <button className="btn btn-primary" onClick={() => report("REG-1001")} disabled={loading}>
              {loading ? "Checking..." : "Test Scan"}
            </button>
          </>
        ) : (
          <button className="btn btn-primary" style={{ width: '100%' }} onClick={() => setScanning(true)}>
            Start Camera Scanner
          </button>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ flex: 1, height: '1px', background: 'var(--border-color)' }} />
        <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>OR</span>
        <div style={{ flex: 1, height: '1px', background: 'var(--border-color)' }} />
      </div>

      <form
        style={{ display: 'flex', gap: '0.5rem' }}
        onSubmit={(e) => {
          e.preventDefault();
          report(manual.trim());
        }}
      >
        <input
          value={manual}
          onChange={(e) => setManual(e.target.value)}
          placeholder="Enter ticket ID (e.g. REG-1001)"
          disabled={loading}
          style={{
            flex: 1,
            padding: '0.75rem 1rem',
            borderRadius: '8px',
            border: '1px solid var(--border-color)',
            background: 'var(--bg-secondary)',
            color: 'var(--text-primary)'
          }}
        />
        <button className="btn btn-secondary" type="submit" disabled={!manual.trim() || loading}>
          Verify
        </button>
      </form>

      {result && (
        <div 
          className="animate-fade-up"
          style={{
            padding: '1rem',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '1rem',
            background: result.success ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
            border: `1px solid ${result.success ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`
          }}
        >
          {result.success ? (
            <CheckCircle color="rgb(34, 197, 94)" style={{ flexShrink: 0 }} />
          ) : (
            <XCircle color="rgb(239, 68, 68)" style={{ flexShrink: 0 }} />
          )}
          <div>
            <strong style={{ display: 'block', color: result.success ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)' }}>
              {result.success ? "Check-in Successful" : "Check-in Failed"}
            </strong>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              {result.message} <br />
              <span style={{ opacity: 0.7 }}>Ticket: {result.code} at {result.time}</span>
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
