<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const email = ref('a.verma@mospi.gov.in')
const password = ref('')
const loading = ref(false)

function handleSignIn() {
  // TODO: swap this for a real POST /api/auth/login call once the backend
  // route is available, and store the returned session/token before
  // navigating to the dashboard.
  loading.value = true
  setTimeout(() => {
    loading.value = false
    router.push('/dashboard')
  }, 400)
}
</script>

<template>
  <div class="pm-login-shell">
    <div class="bg-white rounded-4 shadow-lg p-4 p-md-5" style="width: 100%; max-width: 380px">
      <div class="d-flex align-items-center gap-2 mb-4">
        <div class="brand-icon" style="width: 40px; height: 40px; font-size: 20px">
          <i class="bi bi-shield-fill"></i>
        </div>
        <div>
          <div class="fw-bold" style="font-size: 1rem">PUBLIC MONEY</div>
          <div class="text-muted" style="font-size: 0.68rem; letter-spacing: 0.04em">
            MPLADS AUDIT INTELLIGENCE
          </div>
        </div>
      </div>

      <h5 class="fw-bold mb-1">Sign in to your workspace</h5>
      <p class="text-muted small mb-4">
        Government &amp; audit access only. Use your registered employee credentials.
      </p>

      <form @submit.prevent="handleSignIn">
        <div class="mb-3">
          <label class="form-label small fw-semibold">Employee ID / Email</label>
          <input v-model="email" type="text" class="form-control" placeholder="you@mospi.gov.in" />
        </div>

        <div class="mb-4">
          <label class="form-label small fw-semibold">Password</label>
          <input v-model="password" type="password" class="form-control" placeholder="Enter password" />
        </div>

        <button type="submit" class="btn btn-dark w-100 d-flex align-items-center justify-content-center gap-2" :disabled="loading">
          <i class="bi bi-chevron-right"></i>
          {{ loading ? 'Signing in...' : 'Sign in' }}
        </button>
      </form>

      <p class="text-center text-muted mt-4 mb-0" style="font-size: 0.72rem">
        Team Vertex &middot; Grand Hack IPEC 2026 &middot; Prototype built for SIH26102 (MoSPI)
        <br />
        This is a hackathon concept demo &mdash; not a live government system.
      </p>
    </div>
  </div>
</template>
