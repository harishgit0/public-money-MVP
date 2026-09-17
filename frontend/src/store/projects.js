import { reactive } from 'vue'
import { fetchProjects } from '../api'

// Singleton reactive state (module-level, so every component that imports
// this gets the SAME object — a poor-man's store without needing Pinia).
const state = reactive({
  items: [],
  loaded: false,
  loading: false,
  error: null
})

let inFlight = null

export function useProjectStore() {
  function ensureLoaded() {
    if (state.loaded || inFlight) return inFlight

    state.loading = true
    inFlight = fetchProjects()
      .then((data) => {
        state.items = data
        state.loaded = true
        state.error = null
      })
      .catch((err) => {
        state.error = err.message || 'Could not reach the backend.'
      })
      .finally(() => {
        state.loading = false
        inFlight = null
      })

    return inFlight
  }

  function refresh() {
    state.loaded = false
    return ensureLoaded()
  }

  return { state, ensureLoaded, refresh }
}
