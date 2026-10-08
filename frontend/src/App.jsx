import { Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";

import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import Events from "./pages/Events.jsx";
import EventDetails from "./pages/EventDetails.jsx";
import MyRegistrations from "./pages/MyRegistrations.jsx";
import ManageEvents from "./pages/ManageEvents.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Unauthorized from "./pages/Unauthorized.jsx";

export default function App() {
  return (
    <div className="app-shell">
      <a href="#main-content" className="skip-link">Skip to content</a>
      <Navbar />
      <main id="main-content" className="app-main" tabIndex={-1}>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<Navigate to="/events" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/events" element={<Events />} />
          <Route path="/events/:id" element={<EventDetails />} />
          <Route path="/unauthorized" element={<Unauthorized />} />

          {/* Student only */}
          <Route
            path="/my-registrations"
            element={
              <ProtectedRoute allowedRoles={["student"]}>
                <MyRegistrations />
              </ProtectedRoute>
            }
          />

          {/* Organizer + Admin */}
          <Route
            path="/manage-events"
            element={
              <ProtectedRoute allowedRoles={["organizer", "admin"]}>
                <ManageEvents />
              </ProtectedRoute>
            }
          />

          {/* Any logged-in user (content changes by role) */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute allowedRoles={["student", "organizer", "admin"]}>
                <Dashboard />
              </ProtectedRoute>
            }
          />

          <Route path="*" element={<Navigate to="/events" replace />} />
        </Routes>
      </main>
      <footer className="app-footer">
        © {new Date().getFullYear()} revents · College Event Management Platform
      </footer>
    </div>
  );
}
