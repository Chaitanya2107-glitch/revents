import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { User, Lock, Mail, Building2, Briefcase } from "lucide-react";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    email: "",
    department: "",
    role: "student",
    password: "",
    confirm: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.password !== form.confirm) {
      setError("Passwords do not match.");
      return;
    }
    if (form.password.length < 12) {
      setError("Password must be at least 12 characters long.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await register({
        full_name: form.name,
        email: form.email,
        password: form.password,
        department: form.department || undefined,
        role: form.role
      });
      navigate("/dashboard");
    } catch (err) {
      // Show better error messages
      const msg = err.message || "Registration failed.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth">
      <form className="card form" style={{ maxWidth: '440px', margin: '40px auto' }} onSubmit={handleSubmit}>
        <div style={{ textAlign: 'center', marginBottom: '16px' }}>
          <h2 style={{ fontSize: '1.75rem', marginBottom: '8px' }}>Create your account</h2>
          <p className="muted">Join your campus community in under a minute.</p>
        </div>

        {error && <div className="alert alert--error" role="alert">{error}</div>}

        <div className="field">
          <label htmlFor="name">Full name</label>
          <div style={{ position: 'relative' }}>
            <User size={16} className="text-muted" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
            <input id="name" name="name" value={form.name} onChange={handleChange} style={{ paddingLeft: '36px' }} required />
          </div>
        </div>

        <div className="field">
          <label htmlFor="email">Email address</label>
          <div style={{ position: 'relative' }}>
            <Mail size={16} className="text-muted" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
            <input id="email" type="email" name="email" value={form.email} onChange={handleChange} style={{ paddingLeft: '36px' }} required />
          </div>
        </div>

        <div className="form__grid" style={{ gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div className="field">
            <label htmlFor="department">Department</label>
            <div style={{ position: 'relative' }}>
              <Building2 size={16} className="text-muted" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input id="department" name="department" value={form.department} onChange={handleChange} placeholder="e.g. CSE" style={{ paddingLeft: '36px' }} />
            </div>
          </div>
          <div className="field">
            <label htmlFor="role">I am a</label>
            <div style={{ position: 'relative' }}>
              <Briefcase size={16} className="text-muted" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <select id="role" name="role" value={form.role} onChange={handleChange} style={{ paddingLeft: '36px', appearance: 'none' }}>
                <option value="student">Student</option>
                <option value="organizer">Organizer</option>
              </select>
            </div>
          </div>
        </div>

        <div className="form__grid" style={{ gridTemplateColumns: '1fr', gap: '16px' }}>
          <div className="field">
            <label htmlFor="password">Password</label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} className="text-muted" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input id="password" type="password" name="password" value={form.password} onChange={handleChange} minLength={12} style={{ paddingLeft: '36px' }} required />
            </div>
            <small className="muted" style={{ fontSize: '0.75rem', marginTop: '4px' }}>Must be at least 12 characters</small>
          </div>
          <div className="field">
            <label htmlFor="confirm">Confirm password</label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} className="text-muted" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input id="confirm" type="password" name="confirm" value={form.confirm} onChange={handleChange} minLength={12} style={{ paddingLeft: '36px' }} required />
            </div>
          </div>
        </div>

        <button className="btn btn--primary btn--block" type="submit" disabled={loading} style={{ marginTop: '8px' }}>
          {loading ? "Signing up..." : "Sign up"}
        </button>
        <p className="muted small center" style={{ marginTop: '16px' }}>
          Already have an account? <Link to="/login" style={{ color: 'var(--brand)', fontWeight: 500 }}>Log in</Link>
        </p>
      </form>
    </section>
  );
}
