import { useRef, useState } from "react";
import { NavLink, Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { Menu, X, LogOut, Zap, LayoutDashboard, CalendarDays, KeyRound, Ticket } from "lucide-react";

export default function Navbar() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const toggleRef = useRef(null);
  const navigate = useNavigate();

  const close = () => setOpen(false);
  const handleLogout = () => {
    logout();
    close();
    navigate("/login");
  };

  const links = [{ to: "/events", label: "Events", icon: CalendarDays }];
  if (user) links.push({ to: "/dashboard", label: "Dashboard", icon: LayoutDashboard });
  if (user?.role === "student") links.push({ to: "/my-registrations", label: "Tickets", icon: Ticket });
  if (user?.role === "organizer" || user?.role === "admin")
    links.push({ to: "/manage-events", label: "Manage Events", icon: Zap });

  const displayName = user ? (user.full_name || user.name || (user.email ? user.email.split('@')[0] : "User")) : "";
  return (
    <header className="navbar">
      <div className="navbar__inner container">
        <Link to="/" className="navbar__brand" onClick={close}>
          <div className="navbar__logo"><Zap size={14} /></div> revents
        </Link>

        <button
          ref={toggleRef}
          type="button"
          className="navbar__toggle"
          aria-label={open ? "Close navigation" : "Open navigation"}
          aria-controls="campus-navigation"
          aria-expanded={open}
          onClick={() => setOpen((o) => !o)}
        >
          {open ? <X size={24} /> : <Menu size={24} />}
        </button>

        <nav
          id="campus-navigation"
          aria-label="Main navigation"
          className={`navbar__menu ${open ? "is-open" : ""}`}
          onKeyDown={(event) => {
            if (event.key === "Escape" && open) {
              close();
              toggleRef.current?.focus();
            }
          }}
        >
          <ul className="navbar__links">
            {links.map((l) => {
              const Icon = l.icon;
              return (
                <li key={l.to}>
                  <NavLink
                    to={l.to}
                    onClick={close}
                    className={({ isActive }) => (isActive ? "navlink active" : "navlink")}
                    style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
                  >
                    <Icon size={14} />
                    {l.label}
                  </NavLink>
                </li>
              );
            })}
          </ul>

          <div className="navbar__actions">
            {user ? (
              <>
                <span className="user-chip">
                  <span className="avatar">{displayName[0].toUpperCase()}</span>
                  <span style={{fontWeight: 500, fontSize: '0.875rem', paddingRight: '8px'}}>{displayName}</span>
                </span>
                <button className="btn btn--ghost btn--sm" onClick={handleLogout} title="Logout">
                  <LogOut size={16} />
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn btn--ghost btn--sm" onClick={close}>
                  Log in
                </Link>
                <Link to="/register" className="btn btn--primary btn--sm" onClick={close}>
                  Sign up
                </Link>
              </>
            )}
          </div>
        </nav>
      </div>
    </header>
  );
}
