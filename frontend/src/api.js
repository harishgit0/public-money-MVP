// Talks to the actual backend (app.py / models.py your teammate committed).
// Only two routes exist right now:
//   GET /api/projects        -> list of every project
//   GET /api/projects/<id>   -> one project, looked up by its numeric `id` PK
//                                (NOT unique_work_number)
//
// In dev, vite.config.js proxies /api/* to http://127.0.0.1:5000, so these
// calls work as long as `python app.py` is running locally alongside
// `npm run dev`.

async function request(path) {
  const res = await fetch(path)
  if (!res.ok) {
    throw new Error(`Request to ${path} failed with status ${res.status}`)
  }
  return res.json()
}

export function fetchProjects() {
  return request('/api/projects')
}

export function fetchProject(id) {
  return request(`/api/projects/${id}`)
}
