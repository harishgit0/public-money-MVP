<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchProject } from '../api'
import { useProjectStore } from '../store/projects'
import { formatINR, riskTier } from '../utils/format'

const route = useRoute()
const router = useRouter()
const { state, ensureLoaded } = useProjectStore()

const project = ref(null)
const loading = ref(true)
const error = ref(null)
const note = ref('')

onMounted(async () => {
  await ensureLoaded() // for the peer-average comparison below
  try {
    project.value = await fetchProject(route.params.id)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})

// Signal contributions, straight from the three model columns.
// Values are assumed to be 0-1 scores from the risk engine; if your
// teammate's model outputs a different scale, adjust the *100 below.
const signals = computed(() => {
  if (!project.value) return []
  const p = project.value
  return [
    { label: 'Cost anomaly', value: p.cost_anomaly },
    { label: 'Contractor concentration', value: p.agency_concentration },
    { label: 'Text similarity', value: p.text_similarity }
  ]
    .filter((s) => s.value !== null && s.value !== undefined)
    .map((s) => ({ ...s, pct: Math.min(100, Math.round(s.value * 100)) }))
    .sort((a, b) => b.pct - a.pct)
})

// Peer average cost within the same work_category, computed from the full
// project list already loaded by the store (no dedicated backend endpoint
// for this exists yet).
const peerComparison = computed(() => {
  if (!project.value || !state.loaded) return null
  const peers = state.items.filter(
    (p) => p.work_category === project.value.work_category && p.id !== project.value.id
  )
  if (!peers.length) return null
  const avg = peers.reduce((s, p) => s + (p.sanction_amount || 0), 0) / peers.length
  const deviation = avg ? (((project.value.sanction_amount || 0) - avg) / avg) * 100 : 0
  return { avg: formatINR(avg), deviationPct: deviation.toFixed(0) }
})

function saveNote() {
  // TODO: no POST endpoint for reviewer notes exists in the backend yet.
  // Wire this up once one does — for now it's local-only and resets on reload.
  note.value = ''
}
</script>

<template>
  <div class="pm-content">
    <a href="#" class="text-decoration-none text-muted small" @click.prevent="router.push('/flagged')">
      &lsaquo; Back to flagged projects
    </a>

    <div v-if="error" class="alert alert-danger mt-3">
      Couldn't load project {{ route.params.id }} ({{ error }}).
    </div>
    <div v-else-if="loading" class="text-muted mt-3">Loading project...</div>

    <template v-else-if="project">
      <div class="d-flex justify-content-between align-items-start mt-2 mb-4">
        <div>
          <h5 class="fw-bold mb-1">{{ project.unique_work_number }} &middot; {{ project.work_name }}</h5>
          <p class="text-muted small mb-0">
            {{ project.constituency }}, {{ project.state }} &middot;
            <span class="fw-semibold">{{ formatINR(project.sanction_amount) }} sanctioned</span>
            <span class="pm-status in-review ms-2">{{ project.work_status || 'Unknown status' }}</span>
          </p>
        </div>
        <div class="d-flex gap-2">
          <button class="btn btn-outline-secondary btn-sm">Export report</button>
          <button class="btn btn-danger btn-sm">Escalate to audit team</button>
        </div>
      </div>

      <div class="row g-3">
        <div class="col-lg-8">
          <div class="pm-card mb-3">
            <div class="d-flex align-items-center gap-3 mb-4">
              <div
                class="rounded-circle border border-4 d-flex align-items-center justify-content-center fw-bold"
                style="width: 70px; height: 70px; border-color: #111827 !important; font-size: 1.4rem"
              >
                {{ Math.round(project.risk_score || 0) }}
              </div>
              <div>
                <div class="text-muted small">
                  Risk score / 100 &middot;
                  <span class="pm-score" :class="riskTier(project)">{{ project.risk_level || riskTier(project) }}</span>
                </div>
              </div>
            </div>

            <div class="text-uppercase text-muted small fw-semibold mb-3" style="letter-spacing: 0.05em">
              Signal contributions
            </div>

            <div v-if="!signals.length" class="text-muted small mb-3">
              No signal scores recorded for this project yet.
            </div>
            <div v-for="s in signals" :key="s.label" class="mb-3">
              <div class="d-flex justify-content-between">
                <span class="fw-semibold small">{{ s.label }}</span>
                <span class="text-warning small fw-semibold">{{ s.pct }}%</span>
              </div>
              <div class="progress" style="height: 6px">
                <div class="progress-bar bg-warning" :style="{ width: s.pct + '%' }"></div>
              </div>
            </div>

            <div class="bg-dark text-white rounded-3 p-3 mt-4" v-if="project.reasons">
              <div class="text-warning small fw-semibold mb-2">WHY THIS WAS FLAGGED</div>
              <div class="small">{{ project.reasons }}</div>
            </div>
          </div>
        </div>

        <div class="col-lg-4">
          <div class="pm-card mb-3">
            <div class="text-uppercase text-muted small fw-semibold mb-3" style="letter-spacing: 0.05em">
              Project details
            </div>
            <div class="d-flex justify-content-between small mb-2">
              <span class="text-muted">Category</span><span class="fw-semibold">{{ project.work_category }}</span>
            </div>
            <div class="d-flex justify-content-between small mb-2">
              <span class="text-muted">Sanctioning MP</span><span class="fw-semibold">{{ project.mp_name }}</span>
            </div>
            <div class="d-flex justify-content-between small mb-2">
              <span class="text-muted">Implementing agency</span>
              <span class="fw-semibold">{{ project.implementing_agency_name }}</span>
            </div>
            <div class="d-flex justify-content-between small mb-2">
              <span class="text-muted">Approved on</span>
              <span class="fw-semibold">{{ project.date_of_administrative_approval || '\u2014' }}</span>
            </div>
            <div class="d-flex justify-content-between small mb-2">
              <span class="text-muted">Expected completion</span>
              <span class="fw-semibold">{{ project.expected_completion_date || '\u2014' }}</span>
            </div>
            <template v-if="peerComparison">
              <div class="d-flex justify-content-between small mb-2">
                <span class="text-muted">Peer avg. cost ({{ project.work_category }})</span>
                <span class="fw-semibold">{{ peerComparison.avg }}</span>
              </div>
              <div class="d-flex justify-content-between small">
                <span class="text-muted">Cost deviation</span>
                <span class="fw-semibold" :class="peerComparison.deviationPct > 0 ? 'text-danger' : 'text-success'">
                  {{ peerComparison.deviationPct > 0 ? '+' : '' }}{{ peerComparison.deviationPct }}%
                </span>
              </div>
            </template>
          </div>

          <div class="pm-card">
            <div class="text-uppercase text-muted small fw-semibold mb-2" style="letter-spacing: 0.05em">
              Add reviewer note
            </div>
            <p class="text-muted small">
              Not saved to the backend yet &mdash; there's no notes endpoint in the current schema.
            </p>
            <textarea
              v-model="note"
              class="form-control mb-2"
              rows="3"
              placeholder="Record what you checked and why..."
            ></textarea>
            <button class="btn btn-dark w-100" @click="saveNote">Save note (local only)</button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
