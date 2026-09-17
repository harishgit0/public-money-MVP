<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { currentUser } from '../config'
import { useProjectStore } from '../store/projects'
import { computeDashboard, computeDistricts } from '../utils/derive'

const router = useRouter()
const { state, ensureLoaded } = useProjectStore()
const chartCanvas = ref(null)
let chartInstance = null

const dashboard = computed(() =>
  state.loaded ? computeDashboard(state.items) : null
)
const districts = computed(() => (state.loaded ? computeDistricts(state.items) : []))

function goToProject(id) {
  router.push(`/flagged/${id}`)
}

function renderChart() {
  if (!dashboard.value || !chartCanvas.value) return
  if (chartInstance) chartInstance.destroy()
  const { riskDistribution } = dashboard.value
  chartInstance = new window.Chart(chartCanvas.value, {
    type: 'bar',
    data: {
      labels: riskDistribution.labels,
      datasets: [
        {
          data: riskDistribution.values,
          backgroundColor: riskDistribution.colors,
          borderRadius: 4,
          maxBarThickness: 46
        }
      ]
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, grid: { color: '#f1f3f6' } },
        x: { grid: { display: false } }
      }
    }
  })
}

onMounted(async () => {
  await ensureLoaded()
  renderChart()
})

watch(dashboard, renderChart)
</script>

<template>
  <div class="pm-content">
    <h4 class="fw-bold mb-0">Good morning, {{ currentUser.name.split(' ')[0] }}</h4>
    <p class="text-muted small mb-4">{{ currentUser.region }}</p>

    <div v-if="state.error" class="alert alert-danger">
      Couldn't reach the backend at <code>/api/projects</code> ({{ state.error }}).
      Make sure <code>python app.py</code> is running on port 5000.
    </div>
    <div v-else-if="state.loading" class="text-muted">Loading projects...</div>

    <template v-else-if="dashboard">
      <!-- Stat cards -->
      <div class="row g-3 mb-4">
        <div class="col-md-3">
          <div class="pm-card h-100">
            <div class="text-muted small">Projects ingested</div>
            <div class="pm-stat-value">{{ dashboard.stats.projectsIngested }}</div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="pm-card h-100">
            <div class="text-muted small">High-risk flags <span class="text-muted">(score \u2265 60)</span></div>
            <div class="pm-stat-value">{{ dashboard.stats.highRiskFlags }}</div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="pm-card h-100">
            <div class="text-muted small">Flagged value</div>
            <div class="pm-stat-value">{{ dashboard.stats.flaggedValue }}</div>
            <div class="text-muted small">{{ dashboard.stats.flaggedPct }}% of total spend</div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="pm-card h-100">
            <div class="text-muted small">Avg. risk score</div>
            <div class="pm-stat-value">{{ dashboard.stats.avgRiskScore }}</div>
          </div>
        </div>
      </div>

      <div class="row g-3 mb-4">
        <!-- Highest priority table -->
        <div class="col-lg-7">
          <div class="pm-card h-100">
            <h6 class="fw-bold mb-3">Highest priority right now</h6>
            <table class="pm-table">
              <thead>
                <tr>
                  <th>Project</th>
                  <th>District</th>
                  <th>Cost</th>
                  <th>Signal</th>
                  <th>Score</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p in dashboard.priority" :key="p.id" @click="goToProject(p.id)">
                  <td>
                    <div class="fw-semibold">{{ p.code }}</div>
                    <div class="text-muted small">{{ p.title }}</div>
                  </td>
                  <td>{{ p.district }}</td>
                  <td>{{ p.cost }}</td>
                  <td class="text-muted small">{{ p.signal }}</td>
                  <td><span class="pm-score" :class="p.tier">{{ p.score }}</span></td>
                  <td><i class="bi bi-chevron-right text-muted"></i></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Risk score distribution chart -->
        <div class="col-lg-5">
          <div class="pm-card h-100">
            <h6 class="fw-bold mb-3">Risk score distribution</h6>
            <canvas ref="chartCanvas" height="180"></canvas>
            <div class="d-flex gap-3 mt-2 small text-muted">
              <span><span class="badge rounded-pill" style="background:#16a34a">&nbsp;</span> Low</span>
              <span><span class="badge rounded-pill" style="background:#9ca3af">&nbsp;</span> Medium</span>
              <span><span class="badge rounded-pill" style="background:#d97706">&nbsp;</span> High</span>
              <span><span class="badge rounded-pill" style="background:#111827">&nbsp;</span> Critical</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Districts to watch -->
      <div class="pm-card" v-if="districts.length">
        <h6 class="fw-bold mb-3">Districts to watch</h6>
        <table class="pm-table">
          <thead>
            <tr>
              <th>District</th>
              <th>Projects</th>
              <th>Flagged</th>
              <th>Flag rate</th>
              <th>Dominant signal</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="d in districts" :key="d.district">
              <td class="fw-semibold">{{ d.district }}</td>
              <td>{{ d.projects }}</td>
              <td>{{ d.flagged }}</td>
              <td>{{ d.rate }}</td>
              <td class="text-muted">{{ d.signal }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>
