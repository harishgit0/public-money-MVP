<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useProjectStore } from '../store/projects'
import { computeAnalytics } from '../utils/derive'

const { state, ensureLoaded } = useProjectStore()
const flagsChart = ref(null)
const districtChart = ref(null)
const signalChart = ref(null)
let charts = []

const analytics = computed(() => (state.loaded ? computeAnalytics(state.items) : null))

function destroyCharts() {
  charts.forEach((c) => c.destroy())
  charts = []
}

function renderCharts() {
  if (!analytics.value) return
  destroyCharts()
  const a = analytics.value

  charts.push(
    new window.Chart(flagsChart.value, {
      type: 'line',
      data: {
        labels: a.sanctionsByMonth.labels,
        datasets: [
          {
            data: a.sanctionsByMonth.values,
            borderColor: '#d97706',
            backgroundColor: 'rgba(217,119,6,0.12)',
            fill: true,
            tension: 0.35,
            pointRadius: 2
          }
        ]
      },
      options: {
        plugins: { legend: { display: false } },
        scales: { y: { grid: { color: '#f1f3f6' }, beginAtZero: true }, x: { grid: { display: false } } }
      }
    })
  )

  charts.push(
    new window.Chart(districtChart.value, {
      type: 'bar',
      data: {
        labels: a.byDistrict.labels,
        datasets: [{ data: a.byDistrict.values, backgroundColor: '#111827', borderRadius: 4 }]
      },
      options: {
        indexAxis: 'y',
        plugins: { legend: { display: false } },
        scales: { x: { grid: { color: '#f1f3f6' }, beginAtZero: true }, y: { grid: { display: false } } }
      }
    })
  )

  charts.push(
    new window.Chart(signalChart.value, {
      type: 'doughnut',
      data: {
        labels: a.signalMix.labels,
        datasets: [{ data: a.signalMix.values, backgroundColor: a.signalMix.colors }]
      },
      options: {
        plugins: { legend: { position: 'bottom', labels: { boxWidth: 10 } } },
        cutout: '65%'
      }
    })
  )
}

onMounted(async () => {
  await ensureLoaded()
  renderCharts()
})
watch(analytics, renderCharts)
</script>

<template>
  <div class="pm-content">
    <h4 class="fw-bold mb-1">Analytics &amp; trends</h4>
    <p class="text-muted small mb-4">Computed live from the projects currently in the database</p>

    <div v-if="state.error" class="alert alert-danger">
      Couldn't reach the backend at <code>/api/projects</code> ({{ state.error }}).
    </div>
    <div v-else-if="state.loading" class="text-muted">Loading projects...</div>

    <template v-else-if="analytics">
      <div class="row g-3 mb-3">
        <div class="col-lg-6">
          <div class="pm-card h-100">
            <div class="d-flex justify-content-between">
              <h6 class="fw-bold">Projects sanctioned by month</h6>
              <span class="text-muted small">last 6 months in data</span>
            </div>
            <p class="text-muted small mb-2">
              Based on <code>date_of_administrative_approval</code> \u2014 there's no separate
              "flag raised at" timestamp in the schema yet.
            </p>
            <canvas ref="flagsChart" height="200"></canvas>
          </div>
        </div>
        <div class="col-lg-6">
          <div class="pm-card h-100">
            <div class="d-flex justify-content-between">
              <h6 class="fw-bold">Flagged projects by district</h6>
              <span class="text-muted small">top 6</span>
            </div>
            <canvas ref="districtChart" height="200"></canvas>
          </div>
        </div>
      </div>

      <div class="row g-3">
        <div class="col-lg-6">
          <div class="pm-card h-100">
            <div class="d-flex justify-content-between">
              <h6 class="fw-bold">Signal contribution mix</h6>
              <span class="text-muted small">avg. across all projects</span>
            </div>
            <canvas ref="signalChart" height="200"></canvas>
          </div>
        </div>
        <div class="col-lg-6">
          <div class="pm-card h-100">
            <div class="d-flex justify-content-between mb-3">
              <h6 class="fw-bold">Dataset summary</h6>
            </div>
            <p class="text-muted small">
              The model-validation numbers (recall/precision/false-flag rate) from the wireframe
              aren't in the current schema \u2014 there's no held-out test set stored anywhere.
              Showing real dataset totals instead until that exists.
            </p>
            <div class="row g-2 text-center">
              <div class="col-6">
                <div class="border rounded-3 py-3">
                  <div class="fw-bold" style="font-size: 1.4rem">{{ analytics.summary.totalProjects }}</div>
                  <div class="text-muted small">Total projects</div>
                </div>
              </div>
              <div class="col-6">
                <div class="border rounded-3 py-3">
                  <div class="fw-bold" style="font-size: 1.4rem">{{ analytics.summary.totalSanctioned }}</div>
                  <div class="text-muted small">Total sanctioned</div>
                </div>
              </div>
              <div class="col-6">
                <div class="border rounded-3 py-3">
                  <div class="fw-bold" style="font-size: 1.4rem">{{ analytics.summary.states }}</div>
                  <div class="text-muted small">States covered</div>
                </div>
              </div>
              <div class="col-6">
                <div class="border rounded-3 py-3">
                  <div class="fw-bold" style="font-size: 1.4rem">{{ analytics.summary.avgRiskScore }}</div>
                  <div class="text-muted small">Avg. risk score</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
