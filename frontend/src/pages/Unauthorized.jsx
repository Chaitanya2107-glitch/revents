import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { ShieldAlert } from "lucide-react";

export default function Unauthorized() {
  const { user } = useAuth();

  return (
    <section 
      className="container page animate-fade-up" 
      style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center', 
        justifyContent: 'center',
        minHeight: '60vh',
        textAlign: 'center'
      }}
    >
      <div 
        style={{ 
          width: '80px', height: '80px', borderRadius: '50%', background: 'rgba(239, 68, 68, 0.1)', 
          display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '2rem' 
        }}
      >
        <ShieldAlert size={40} color="rgb(239, 68, 68)" />
      </div>
      
      <h1 style={{ fontSize: '2.5rem', fontWeight: 700, marginBottom: '1rem', letterSpacing: '-0.02em' }}>
        Access Denied
      </h1>
      
      <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem', maxWidth: '400px', marginBottom: '2.5rem', lineHeight: 1.6 }}>
        {user
          ? `Your current role (${user.role}) doesn't have the necessary permissions to access this area.`
          : "Please log in to continue accessing the platform."}
      </p>
      
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
        <Link to="/events" className="btn btn-ghost">
          Browse Events
        </Link>
        <Link to={user ? "/dashboard" : "/login"} className="btn btn-primary">
          {user ? "Go to Dashboard" : "Log In Now"}
        </Link>
      </div>
    </section>
  );
}
