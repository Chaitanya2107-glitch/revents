export const CATEGORIES = ["All", "Technical", "Cultural", "Sports", "Workshop", "Seminar"];

export const events = [
  {
    id: 1,
    title: "HackSphere 2026 – 24h Hackathon",
    category: "Technical",
    date: "2026-11-14",
    time: "09:00 AM",
    venue: "Innovation Lab, Block C",
    organizer: "Coding Club",
    capacity: 150,
    registered: 112,
    price: 0,
    hue: 250,
    description:
      "Build, break and ship in 24 hours. Teams of up to four compete for prizes across AI, web and sustainability tracks. Mentors from industry will be around all night.",
  },
  {
    id: 2,
    title: "Rhythm & Roots – Annual Cultural Fest",
    category: "Cultural",
    date: "2026-11-22",
    time: "05:00 PM",
    venue: "Main Auditorium",
    organizer: "Cultural Committee",
    capacity: 800,
    registered: 540,
    price: 100,
    hue: 330,
    description:
      "An evening of dance, music and drama performed by students from every department, followed by a food street and open-mic.",
  },
  {
    id: 3,
    title: "Inter-College Football Cup",
    category: "Sports",
    date: "2026-12-03",
    time: "08:30 AM",
    venue: "University Ground",
    organizer: "Sports Council",
    capacity: 300,
    registered: 188,
    price: 50,
    hue: 150,
    description:
      "Sixteen colleges, one trophy. Knockout format with the final on day three. Spectators are welcome and entry is free for registered students.",
  },
  {
    id: 4,
    title: "React & Modern Frontend Workshop",
    category: "Workshop",
    date: "2026-10-28",
    time: "10:00 AM",
    venue: "Seminar Hall 2",
    organizer: "Web Dev Society",
    capacity: 60,
    registered: 58,
    price: 0,
    hue: 200,
    description:
      "A hands-on session covering components, hooks, routing and state management. Bring your laptop; starter code will be shared before the session.",
  },
  {
    id: 5,
    title: "Careers in AI – Guest Lecture",
    category: "Seminar",
    date: "2026-11-05",
    time: "02:00 PM",
    venue: "Conference Room A",
    organizer: "Placement Cell",
    capacity: 200,
    registered: 96,
    price: 0,
    hue: 30,
    description:
      "Alumni working at leading AI labs talk about breaking into the field, what to learn now and how to build a portfolio recruiters notice.",
  },
  {
    id: 6,
    title: "Photography Walk & Contest",
    category: "Cultural",
    date: "2026-11-09",
    time: "06:30 AM",
    venue: "Campus Lake Gate",
    organizer: "Photography Club",
    capacity: 80,
    registered: 41,
    price: 0,
    hue: 180,
    description:
      "Capture the campus at sunrise. Submit your three best frames by the evening; winners are announced at the next club meet.",
  },
];

// Events a (dummy) student has registered for
export const registrations = [
  { id: "REG-1001", eventId: 1, status: "Confirmed", registeredOn: "2026-10-02", attended: false },
  { id: "REG-1002", eventId: 4, status: "Confirmed", registeredOn: "2026-10-05", attended: false },
  { id: "REG-1003", eventId: 5, status: "Waitlisted", registeredOn: "2026-10-06", attended: false },
];

export const feedbackList = [
  { id: 1, eventId: 4, user: "Aarav", rating: 5, comment: "Super practical session, loved the live coding." },
  { id: 2, eventId: 1, user: "Meera", rating: 4, comment: "Great energy, wish there were more snacks!" },
];

// Dashboard numbers per role
export const stats = {
  student: [
    { label: "Registered Events", value: 3 },
    { label: "Attended", value: 7 },
    { label: "Certificates", value: 4 },
    { label: "Upcoming", value: 2 },
  ],
  organizer: [
    { label: "My Events", value: 5 },
    { label: "Total Registrations", value: 412 },
    { label: "Avg. Rating", value: "4.5" },
    { label: "Checked-in Today", value: 38 },
  ],
  admin: [
    { label: "Total Events", value: 42 },
    { label: "Active Users", value: 1860 },
    { label: "Pending Approvals", value: 6 },
    { label: "Organizers", value: 18 },
  ],
};

export const pendingApprovals = [
  { id: 101, title: "Robotics Expo", organizer: "Robotics Club", date: "2026-12-10" },
  { id: 102, title: "Startup Pitch Night", organizer: "E-Cell", date: "2026-12-14" },
  { id: 103, title: "Yoga & Wellness Day", organizer: "Wellness Cell", date: "2026-11-30" },
];

export const formatDate = (iso) =>
  new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
