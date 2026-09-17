# Public Money — Frontend

Vue 3 + Vue Router + Bootstrap 5 frontend, wired to the real Flask backend
(`app.py` + `models.py` your teammate committed). Covers the 6 wireframe
screens: Login, Dashboard, Flagged projects, Project detail, Contractors,
Analytics & trends.

## Run it

You need **both** servers running:

```bash
# Terminal 1 — backend (from wherever app.py / models.py live)
pip install -r requirements.txt
python app.py                 # http://127.0.0.1:5000

# Terminal 2 — frontend (this folder)
npm install
npm run dev                   # http://127.0.0.1:5173
```

`vite.config.js` proxies every `/api/*` request to `http://127.0.0.1:5000`,
so the frontend just calls `fetch('/api/projects')` with no CORS setup
needed on the Flask side. If your teammate runs the backend on a different
port, change the `target` in `vite.config.js`.

If the projects table is empty, run your teammate's `import_data.py` first
(needs `data/mplad_projects.csv` in place) so there's something to fetch.

## How data flows

There are only two real backend routes right now:

- `GET /api/projects` — every project
- `GET /api/projects/<id>` — one project, by its numeric `id` (not `unique_work_number`)

Everything else the wireframe shows (dashboard stats, districts-to-watch,
contractor rollups, analytics charts) is **computed client-side** from the
one `/api/projects` list — see `src/utils/derive.js`. There's no separate
aggregate endpoint yet, so this avoids re-fetching the same data five times
and keeps a single source of truth (`src/store/projects.js`, a tiny reactive
singleton store).

### What changed vs. the original wireframe, and why

The wireframe assumed some data the current schema doesn't have. Rather than
fake it, these were swapped for the closest real equivalent:

| Wireframe element | Why it couldn't be built as-is | What it shows instead |
|---|---|---|
| Review status (Unreviewed/In review/Cleared) | No review-workflow field in `models.py` | The real `work_status` column (e.g. Ongoing/Completed) |
| Review timeline + reviewer notes | No timestamps/notes table exist | Note box is kept but is **local-only** (`// TODO` in `ProjectDetailView.vue` — needs a real notes endpoint) |
| "Similar projects flagged nearby" | `text_similarity` is a single score per project, not a pairwise link to a specific other project | Dropped — would need the backend to store *which* project it's similar to |
| Avg. time to review | No flagged\_at / reviewed\_at timestamps | Replaced with **Avg. risk score** |
| Flags raised per week | No `flagged_at` timestamp | Replaced with **Projects sanctioned by month**, using `date_of_administrative_approval` |
| Contractor 12-month trend sparkline | No per-contractor time series available | Replaced with **Total sanctioned value** per contractor |
| Validation card (91% recall / 84% precision / etc.) | Model-validation metrics aren't stored anywhere in this schema | Replaced with a real **dataset summary** (total projects, total sanctioned, states covered, avg risk score) |

Once the backend grows these fields (a `review_status` column, a
`project_notes` table, a `flagged_at` timestamp, stored model-validation
metrics), swap the relevant bit in `derive.js` / the view for the real
fetch — that's the whole point of keeping all the aggregation in one file.

## Project layout

```
src/
  main.js, App.vue, style.css
  api.js                 # fetch wrapper for /api/projects, /api/projects/:id
  config.js               # static placeholder user (no auth endpoint yet)
  store/projects.js        # shared reactive store — fetches /api/projects once
  utils/format.js          # formatINR, riskTier, isFlagged, statusClass
  utils/derive.js          # dashboard/district/contractor/analytics aggregation
  router/index.js
  components/Sidebar.vue, TopBar.vue
  views/
    LoginView.vue           # still fake — no /api/auth endpoint exists yet
    DashboardView.vue
    FlaggedProjectsView.vue
    ProjectDetailView.vue   # fetches by numeric id + computes peer-cost comparison
    ContractorsView.vue
    AnalyticsView.vue
```

## Known gaps (backend side, not yours to fix in this repo)

- No auth/session endpoint — login is cosmetic only.
- No POST endpoint for reviewer notes.
- No endpoint tying one flagged project to specific similar ones.
- `cost_anomaly` / `agency_concentration` / `text_similarity` are assumed to
  be 0–1 scores in `derive.js` and `ProjectDetailView.vue` — if your
  teammate's risk model actually outputs a different scale, search for
  `* 100` in those two files and adjust.
