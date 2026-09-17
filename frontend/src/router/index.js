import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/login' },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { layout: 'bare' }
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { title: 'Dashboard' }
  },
  {
    path: '/flagged',
    name: 'flagged',
    component: () => import('../views/FlaggedProjectsView.vue'),
    meta: { title: 'Flagged projects' }
  },
  {
    // :id is the numeric `id` primary key from the backend (Project.id),
    // NOT unique_work_number — GET /api/projects/<int:project_id> expects that.
    path: '/flagged/:id',
    name: 'project-detail',
    component: () => import('../views/ProjectDetailView.vue'),
    meta: { title: 'Project detail' }
  },
  {
    path: '/contractors',
    name: 'contractors',
    component: () => import('../views/ContractorsView.vue'),
    meta: { title: 'Contractors' }
  },
  {
    path: '/analytics',
    name: 'analytics',
    component: () => import('../views/AnalyticsView.vue'),
    meta: { title: 'Analytics & trends' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// TODO: there's no auth/session endpoint in the backend yet, so this is a
// pass-through. Once one exists, check the session here before letting
// anything but /login through.
router.beforeEach(() => {
  return true
})

export default router
