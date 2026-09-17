// sanction_amount comes from the backend as a plain float (rupees).
// Format it the way the wireframe shows costs: lakhs (L) / crores (Cr).
export function formatINR(amount) {
  if (amount === null || amount === undefined || Number.isNaN(amount)) return '\u2014'
  const n = Number(amount)
  if (n >= 1e7) return `\u20B9${(n / 1e7).toFixed(2)}Cr`
  if (n >= 1e5) return `\u20B9${(n / 1e5).toFixed(1)}L`
  return `\u20B9${n.toLocaleString('en-IN')}`
}

// risk_level is a string the backend already computed (e.g. "Critical",
// "High", "Medium", "Low"). We just need a CSS-safe lowercase class for the
// pm-score badge. Falls back to score-based buckets if risk_level is missing
// so the UI doesn't break on incomplete rows.
export function riskTier(project) {
  if (project.risk_level) return project.risk_level.toLowerCase()
  const score = project.risk_score ?? 0
  if (score >= 80) return 'critical'
  if (score >= 60) return 'high'
  if (score >= 40) return 'medium'
  return 'low'
}

export function isFlagged(project) {
  return (project.risk_score ?? 0) >= 60
}

// work_status is the project's execution status from the backend
// (e.g. "Ongoing" / "Completed" / "Delayed") — NOT a review workflow status.
// There's no reviewed/in-review/cleared field in the schema yet, so we style
// off whatever string the backend actually sends instead of inventing one.
export function statusClass(workStatus) {
  const s = (workStatus || '').toLowerCase()
  if (s.includes('complete')) return 'cleared'
  if (s.includes('delay') || s.includes('stall')) return 'unreviewed'
  return 'in-review'
}
