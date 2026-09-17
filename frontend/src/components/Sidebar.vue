<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { currentUser } from '../config'
import { useProjectStore } from '../store/projects'
import { isFlagged } from '../utils/format'

const route = useRoute()
const { state, ensureLoaded } = useProjectStore()

onMounted(ensureLoaded)

const flaggedCount = computed(() => state.items.filter(isFlagged).length)

function isActive(name) {
  return route.name === name
}
</script>

<template>
  <aside class="pm-sidebar">
    <div class="brand">
      <div class="brand-icon"><i class="bi bi-shield-fill"></i></div>
      <div>
        <div class="brand-title">PUBLIC MONEY</div>
        <div class="brand-sub">AUDIT INTELLIGENCE</div>
      </div>
    </div>

    <div class="pm-nav-group-label">OVERVIEW</div>
    <router-link to="/dashboard" class="pm-nav-link" :class="{ active: isActive('dashboard') }">
      <i class="bi bi-grid-1x2-fill"></i> Dashboard
    </router-link>

    <div class="pm-nav-group-label">REVIEW QUEUE</div>
    <router-link to="/flagged" class="pm-nav-link" :class="{ active: isActive('flagged') }">
      <i class="bi bi-flag-fill"></i> Flagged projects
      <span class="pm-nav-badge" v-if="flaggedCount">{{ flaggedCount }}</span>
    </router-link>
    <router-link to="/contractors" class="pm-nav-link" :class="{ active: isActive('contractors') }">
      <i class="bi bi-people-fill"></i> Contractors
    </router-link>

    <div class="pm-nav-group-label">INTELLIGENCE</div>
    <router-link to="/analytics" class="pm-nav-link" :class="{ active: isActive('analytics') }">
      <i class="bi bi-bar-chart-fill"></i> Analytics & trends
    </router-link>

    <div class="pm-sidebar-footer">
      <div class="pm-avatar">{{ currentUser.initials }}</div>
      <div>
        <div style="color: #fff; font-size: 0.85rem; font-weight: 600">{{ currentUser.name }}</div>
        <div style="font-size: 0.72rem; color: #94a3b8">
          {{ currentUser.role }} &middot; {{ currentUser.region }}
        </div>
      </div>
      <router-link to="/login" class="ms-auto text-white-50" title="Sign out">
        <i class="bi bi-box-arrow-right"></i>
      </router-link>
    </div>
  </aside>
</template>
