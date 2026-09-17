<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import TopBar from './components/TopBar.vue'

const route = useRoute()
const isBare = computed(() => route.meta.layout === 'bare')
const pageTitle = computed(() => route.meta.title || '')
</script>

<template>
  <!-- Login screen renders full-bleed, no sidebar/topbar -->
  <router-view v-if="isBare" />

  <div v-else class="pm-shell">
    <Sidebar />
    <div class="pm-main">
      <TopBar :title="pageTitle" />
      <router-view />
    </div>
  </div>
</template>
