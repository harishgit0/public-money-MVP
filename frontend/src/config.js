// The backend model/routes you shared don't include auth or a users table
// yet, so there's no real logged-in user to fetch. This stays a static
// placeholder until a /api/auth or /api/me endpoint exists.
export const currentUser = {
  name: 'Ananya Verma',
  initials: 'AV',
  role: 'District Auditor',
  region: 'Delhi NCR'
}
