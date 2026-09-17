import { formatINR, isFlagged, riskTier } from './format'

function groupBy(items, keyFn) {
  const map = new Map()
  for (const item of items) {
    const key = keyFn(item) || 'Unknown'
    if (!map.has(key)) map.set(key, [])
    map.get(key).push(item)
  }
  return map
}

function safeDate(str) {
  const d = new Date(str)
  return Number.isNaN(d.getTime()) ? null : d
}

// ---------- Dashboard ----------
export function computeDashboard(items) {
  const total = items.length
  const flagged = items.filter(isFlagged)
  const totalSanctioned = items.reduce((sum, p) => sum + (p.sanction_amount || 0), 0)
  const flaggedValue = flagged.reduce((sum, p) => sum + (p.sanction_amount || 0), 0)
  const avgRisk = total ? items.reduce((s, p) => s + (p.risk_score || 0), 0) / total : 0

  const priority = [...items]
    .sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0))
    .slice(0, 4)
    .map((p) => ({
      id: p.id,
      code: p.unique_work_number,
      title: p.work_name,
      district: p.constituency,
      cost: formatINR(p.sanction_amount),
      signal: dominantSignalLabel(p),
      score: Math.round(p.risk_score || 0),
      tier: riskTier(p)
    }))

  const buckets = [0, 0, 0, 0, 0] // 0-19, 20-39, 40-59, 60-79, 80-100
  for (const p of items) {
    const score = p.risk_score || 0
    const idx = Math.min(4, Math.floor(score / 20))
    buckets[idx] += 1
  }

  return {
    stats: {
      projectsIngested: total,
      highRiskFlags: flagged.length,
      flaggedValue: formatINR(flaggedValue),
      flaggedPct: totalSanctioned ? ((flaggedValue / totalSanctioned) * 100).toFixed(1) : '0.0',
      avgRiskScore: avgRisk.toFixed(1)
    },
    priority,
    riskDistribution: {
      labels: ['0-19', '20-39', '40-59', '60-79', '80-100'],
      values: buckets,
      colors: ['#16a34a', '#16a34a', '#9ca3af', '#d97706', '#111827']
    }
  }
}

function dominantSignalLabel(p) {
  const signals = [
    ['Cost anomaly', p.cost_anomaly],
    ['Contractor conc.', p.agency_concentration],
    ['Text similarity', p.text_similarity]
  ].filter(([, v]) => v !== null && v !== undefined)

  if (!signals.length) return '\u2014'
  signals.sort((a, b) => b[1] - a[1])
  return signals[0][0]
}

// ---------- Districts to watch ----------
export function computeDistricts(items) {
  const byDistrict = groupBy(items, (p) => p.constituency)
  const rows = []
  for (const [district, projects] of byDistrict) {
    const flagged = projects.filter(isFlagged)
    if (!flagged.length) continue
    rows.push({
      district,
      projects: projects.length,
      flagged: flagged.length,
      rate: `${((flagged.length / projects.length) * 100).toFixed(1)}%`,
      signal: dominantSignalAcross(flagged)
    })
  }
  return rows.sort((a, b) => b.flagged - a.flagged).slice(0, 6)
}

function dominantSignalAcross(projects) {
  const totals = { 'Cost anomaly': 0, 'Contractor concentration': 0, 'Text similarity': 0 }
  for (const p of projects) {
    totals['Cost anomaly'] += p.cost_anomaly || 0
    totals['Contractor concentration'] += p.agency_concentration || 0
    totals['Text similarity'] += p.text_similarity || 0
  }
  return Object.entries(totals).sort((a, b) => b[1] - a[1])[0][0]
}

// ---------- Contractors ----------
export function computeContractors(items) {
  const byAgency = groupBy(items, (p) => p.implementing_agency_name)
  const rows = []
  for (const [name, projects] of byAgency) {
    if (!name || name === 'Unknown') continue
    const flagged = projects.filter(isFlagged)
    const avgRisk = projects.reduce((s, p) => s + (p.risk_score || 0), 0) / projects.length
    const totalSanctioned = projects.reduce((s, p) => s + (p.sanction_amount || 0), 0)
    const districts = new Set(projects.map((p) => p.constituency))
    const categories = new Set(projects.map((p) => p.work_category))

    const dates = projects.map((p) => safeDate(p.date_of_administrative_approval)).filter(Boolean)
    const activeSince = dates.length ? new Date(Math.min(...dates)).getFullYear() : '\u2014'

    rows.push({
      name,
      projects: projects.length,
      districts: districts.size,
      categories: categories.size,
      avgRisk: Math.round(avgRisk),
      tier: avgRisk >= 80 ? 'critical' : avgRisk >= 60 ? 'high' : avgRisk >= 40 ? 'medium' : 'low',
      flagged: flagged.length,
      totalSanctioned: formatINR(totalSanctioned),
      activeSince,
      districtList: [...districts].join(', '),
      categoryList: [...categories].join(', ')
    })
  }
  return rows.sort((a, b) => b.avgRisk - a.avgRisk)
}

export function contractorConcentrationNote(row, allRows) {
  if (!allRows.length) return ''
  const avgProjects = allRows.reduce((s, r) => s + r.projects, 0) / allRows.length
  if (row.projects > avgProjects * 1.5 && row.flagged > 0) {
    return `${row.projects} projects across ${row.districts} district${row.districts === 1 ? '' : 's'} is well above the average of ${avgProjects.toFixed(1)} per contractor. ${row.flagged} of ${row.projects} projects are also flagged \u2014 recommend a combined review rather than per-project.`
  }
  if (row.flagged > 0) {
    return `${row.flagged} of ${row.projects} projects from this contractor are currently flagged. Worth a closer look alongside the individual project reviews.`
  }
  return `No flagged projects from this contractor yet across ${row.projects} project${row.projects === 1 ? '' : 's'}.`
}

// ---------- Analytics ----------
export function computeAnalytics(items) {
  // Bucket by the month of administrative approval (last 6 months present
  // in the data) — there's no "flagged_at" timestamp in the schema, so this
  // tracks sanctions over time rather than a live flag-raising feed.
  const monthTotals = new Map()
  for (const p of items) {
    const d = safeDate(p.date_of_administrative_approval)
    if (!d) continue
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    monthTotals.set(key, (monthTotals.get(key) || 0) + 1)
  }
  const sortedMonths = [...monthTotals.entries()].sort((a, b) => (a[0] > b[0] ? 1 : -1)).slice(-6)

  const byDistrict = groupBy(items, (p) => p.constituency)
  const districtFlagged = [...byDistrict.entries()]
    .map(([district, projects]) => [district, projects.filter(isFlagged).length])
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)

  const totals = { cost: 0, agency: 0, text: 0 }
  for (const p of items) {
    totals.cost += p.cost_anomaly || 0
    totals.agency += p.agency_concentration || 0
    totals.text += p.text_similarity || 0
  }
  const signalSum = totals.cost + totals.agency + totals.text || 1

  const totalSanctioned = items.reduce((s, p) => s + (p.sanction_amount || 0), 0)
  const avgRisk = items.length ? items.reduce((s, p) => s + (p.risk_score || 0), 0) / items.length : 0

  return {
    sanctionsByMonth: {
      labels: sortedMonths.map(([m]) => m),
      values: sortedMonths.map(([, v]) => v)
    },
    byDistrict: {
      labels: districtFlagged.map(([d]) => d),
      values: districtFlagged.map(([, v]) => v)
    },
    signalMix: {
      labels: ['Cost anomaly', 'Contractor concentration', 'Text similarity'],
      values: [totals.cost, totals.agency, totals.text].map((v) => Math.round((v / signalSum) * 100)),
      colors: ['#eab308', '#111827', '#16a34a']
    },
    summary: {
      totalProjects: items.length,
      totalSanctioned: formatINR(totalSanctioned),
      states: new Set(items.map((p) => p.state)).size,
      avgRiskScore: avgRisk.toFixed(1)
    }
  }
}
