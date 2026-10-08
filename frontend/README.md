# CampusConnect – College Event Management (Frontend)

React + Vite frontend with dummy data. No backend, no Supabase.

## Run it

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # production build
```

## Folder structure

```
college-event-management/
├── index.html
├── package.json
├── vite.config.js
└── src/
    ├── main.jsx                 # entry: Router + AuthProvider + styles
    ├── App.jsx                  # route table
    ├── context/
    │   └── AuthContext.jsx      # dummy auth + role state
    ├── data/
    │   └── dummyData.js         # events, registrations, feedback, stats
    ├── components/
    │   ├── Navbar.jsx
    │   ├── EventCard.jsx
    │   ├── EventForm.jsx        # add / edit
    │   ├── FeedbackForm.jsx
    │   ├── QRTicket.jsx         # QR placeholder (not scannable)
    │   ├── QRScanner.jsx        # scanner UI placeholder
    │   └── ProtectedRoute.jsx   # role-based guard
    ├── pages/
    │   ├── Login.jsx
    │   ├── Register.jsx
    │   ├── Events.jsx
    │   ├── EventDetails.jsx
    │   ├── MyRegistrations.jsx
    │   ├── ManageEvents.jsx
    │   ├── Dashboard.jsx
    │   └── Unauthorized.jsx
    └── styles/
        ├── global.css           # tokens, reset, layout helpers
        ├── components.css       # buttons, cards, navbar, forms, QR, table
        └── pages.css            # page-specific layouts
```

## Routes & roles

| Path               | Access                     |
|--------------------|----------------------------|
| `/events`          | Public                     |
| `/events/:id`      | Public                     |
| `/login`, `/register` | Public                  |
| `/dashboard`       | Any logged-in user         |
| `/my-registrations`| Student                    |
| `/manage-events`   | Organizer, Admin           |
| `/unauthorized`    | Shown on denied access     |

**Trying roles:** log in with any email/password and pick a role, or use the
dashed "role" dropdown in the navbar to switch instantly. Try opening
`/manage-events` as a student to see the Unauthorized page.

## Modern UI design suggestions

**Colour palette**
- Primary: indigo `#4f46e5` (hover `#4338ca`, tint `#eef2ff`)
- Accent: teal `#14b8a6`
- Status: success `#16a34a`, warning `#f59e0b`, danger `#dc2626`
- Neutrals: background `#f8fafc`, surface `#ffffff`, text `#0f172a`, muted `#64748b`, border `#e2e8f0`
- Keep ~60% neutral, 30% surface/white, 10% primary/accent so CTAs stand out.

**Typography**
- Headings: Poppins 600/700. Body: Inter 400/500/600.
- Fluid headings with `clamp()`; body 16px, line-height 1.6; secondary text 13–14px.

**Spacing & shape**
- 8px spacing scale (`--space-*`), generous whitespace between sections.
- Radius 8px for controls, 14–20px for cards/hero; soft layered shadows instead of heavy borders.

**Interaction & accessibility**
- One primary button per view; ghost buttons for secondary actions.
- Visible `:focus-visible` rings, `aria-*` on tabs/stars/menu, colour contrast ≥ 4.5:1.
- Subtle motion only (150–200ms hover lifts); respect `prefers-reduced-motion` if you add more.
- Mobile-first: hamburger nav, tables collapse to stacked cards, grids use `auto-fill/minmax`.

## When you add a backend later

- Replace `dummyData.js` imports with API calls inside the pages.
- Swap `AuthContext` login/logout for real auth, and enforce roles on the server too
  (the `ProtectedRoute` guard is UI-only).
- Replace `QRTicket` with a real generator (e.g. `qrcode.react`) and `QRScanner`
  with a camera library (e.g. `html5-qrcode`).
