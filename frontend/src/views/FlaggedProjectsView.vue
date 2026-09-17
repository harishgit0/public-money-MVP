<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '../store/projects'
import { formatINR, isFlagged, riskTier } from '../utils/format'

const router = useRouter()
const { state, ensureLoaded } = useProjectStore()
onMounted(ensureLoaded)

const activeFilter = ref('all')
const page = ref(1)
const pageSize = 7

const filters = [
  { key: 'all', label: 'All' },
  { key: 'high', label: 'Risk \u2265 70' },
  { key: 'medium', label: 'Risk 40-69' },
  { key: 'low', label: 'Risk < 40' }
]

const flagged = computed(() => state.items.filter(isFlagged))

const filtered = computed(() => {
  if (activeFilter.value === 'high') return flagged.value.filter((p) => (p.risk_score || 0) >= 70)
  if (activeFilter.value === 'medium')
    return flagged.value.filter((p) => (p.risk_score || 0) >= 40 && (p.risk_score || 0) < 70)
  if (activeFilter.value === 'low') return flagged.value.filter((p) => (p.risk_score || 0) < 40)
  return flagged.value
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize)))

const paged = computed(() => {
  const start = (page.value - 1) * pageSize
  return filtered.value.slice(start, start + pageSize)
})

function openProject(id) {
  router.push(`/flagged/${id}`)
}
</script>

<template>
  <div class="pm-content">
    <h4 class="fw-bold mb-1">Flagged projects</h4>
    <p class="text-muted small mb-4">{{ filtered.length }} of {{ state.items.length }} projects meet review criteria</p>

    <div v-if="state.error" class="alert alert-danger">
      Couldn't reach the backend at <code>/api/projects</code> ({{ state.error }}).
    </div>
    <div v-else-if="state.loading" class="text-muted">Loading projects...</div>

    <template v-else>
      <div class="d-flex flex-wrap gap-2 mb-3 align-items-center">
        <div class="btn-group">
          <button
            v-for="f in filters"
            :key="f.key"
            class="btn btn-sm"
            :class="activeFilter === f.key ? 'btn-dark' : 'btn-outline-secondary'"
            @click="activeFilter = f.key; page = 1"
          >
            {{ f.label }}
          </button>
        </div>
      </div>

      <div class="pm-card">
        <table class="pm-table">
          <thead>
            <tr>
              <th>Work number</th>
              <th>District</th>
              <th>Category</th>
              <th>Contractor</th>
              <th>Cost</th>
              <th>Risk score</th>
              <th>Work status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in paged" :key="p.id" @click="openProject(p.id)">
              <td class="fw-semibold">{{ p.unique_work_number }}</td>
              <td>{{ p.constituency }}</td>
              <td>{{ p.work_category }}</td>
              <td>{{ p.implementing_agency_name }}</td>
              <td>{{ formatINR(p.sanction_amount) }}</td>
              <td><span class="pm-score" :class="riskTier(p)">{{ Math.round(p.risk_score || 0) }}</span></td>
              <td><span class="pm-status in-review">{{ p.work_status || '\u2014' }}</span></td>
              <td><i class="bi bi-chevron-right text-muted"></i></td>
            </tr>
          </tbody>
        </table>

        <div class="d-flex justify-content-between align-items-center mt-3" v-if="filtered.length">
          <span class="text-muted small">
            Showing {{ (page - 1) * pageSize + 1 }}-{{ Math.min(page * pageSize, filtered.length) }}
            of {{ filtered.length }}
          </span>
          <nav>
            <ul class="pagination pagination-sm mb-0">
              <li class="page-item" :class="{ disabled: page === 1 }">
                <a class="page-link" href="#" @click.prevent="page = Math.max(1, page - 1)">&lsaquo;</a>
              </li>
              <li class="page-item disabled"><span class="page-link">{{ page }} / {{ totalPages }}</span></li>
              <li class="page-item" :class="{ disabled: page === totalPages }">
                <a class="page-link" href="#" @click.prevent="page = Math.min(totalPages, page + 1)">&rsaquo;</a>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    </template>
  </div>
</template>
