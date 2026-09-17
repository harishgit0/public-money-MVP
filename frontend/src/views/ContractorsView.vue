<script setup>
import { computed, onMounted, ref } from 'vue'
import { useProjectStore } from '../store/projects'
import { computeContractors, contractorConcentrationNote } from '../utils/derive'

const { state, ensureLoaded } = useProjectStore()
onMounted(ensureLoaded)

const contractors = computed(() => (state.loaded ? computeContractors(state.items) : []))
const selectedName = ref(null)
const selected = computed(
  () => contractors.value.find((c) => c.name === selectedName.value) || contractors.value[0]
)
const note = computed(() =>
  selected.value ? contractorConcentrationNote(selected.value, contractors.value) : ''
)
</script>

<template>
  <div class="pm-content">
    <h4 class="fw-bold mb-1">Contractors</h4>
    <p class="text-muted small mb-4">Repeat activity and concentration across districts and categories</p>

    <div v-if="state.error" class="alert alert-danger">
      Couldn't reach the backend at <code>/api/projects</code> ({{ state.error }}).
    </div>
    <div v-else-if="state.loading" class="text-muted">Loading projects...</div>

    <template v-else>
      <div class="pm-card mb-4">
        <table class="pm-table">
          <thead>
            <tr>
              <th>Contractor</th>
              <th>Projects</th>
              <th>Districts</th>
              <th>Categories</th>
              <th>Avg. risk score</th>
              <th>Flagged</th>
              <th>Total sanctioned</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in contractors" :key="c.name" @click="selectedName = c.name">
              <td class="fw-semibold">{{ c.name }}</td>
              <td>{{ c.projects }}</td>
              <td>{{ c.districts }}</td>
              <td>{{ c.categories }}</td>
              <td><span class="pm-score" :class="c.tier">{{ c.avgRisk }}</span></td>
              <td><span class="pm-score" :class="c.flagged ? 'high' : 'low'">{{ c.flagged }}</span></td>
              <td>{{ c.totalSanctioned }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="row g-3" v-if="selected">
        <div class="col-lg-6">
          <div class="pm-card h-100">
            <div class="text-uppercase text-muted small fw-semibold mb-3" style="letter-spacing: 0.05em">
              {{ selected.name.toUpperCase() }} &mdash; PROFILE
            </div>
            <div class="d-flex justify-content-between small mb-2">
              <span class="text-muted">Active since (earliest sanction)</span>
              <span class="fw-semibold">{{ selected.activeSince }}</span>
            </div>
            <div class="d-flex justify-content-between small mb-2">
              <span class="text-muted">Total sanctioned value</span>
              <span class="fw-semibold">{{ selected.totalSanctioned }}</span>
            </div>
            <div class="d-flex justify-content-between small mb-2">
              <span class="text-muted">Districts</span>
              <span class="fw-semibold">{{ selected.districtList }}</span>
            </div>
            <div class="d-flex justify-content-between small">
              <span class="text-muted">Categories</span>
              <span class="fw-semibold">{{ selected.categoryList }}</span>
            </div>
          </div>
        </div>
        <div class="col-lg-6">
          <div class="bg-dark text-white rounded-3 p-3 h-100">
            <div class="text-warning small fw-semibold mb-2">CONCENTRATION NOTE</div>
            <div class="small">{{ note }}</div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
