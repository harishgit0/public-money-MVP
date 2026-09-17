<script setup>
import { currentUser } from '../config'

defineProps({
  title: {
    type: String,
    required: true
  }
})
</script>

<template>
  <header class="pm-topbar">
    <h6 class="mb-0 fw-semibold">{{ title }}</h6>

    <div class="d-flex align-items-center gap-3">
      <div class="input-group" style="width: 280px">
        <span class="input-group-text bg-white border-end-0"><i class="bi bi-search"></i></span>
        <input
          type="text"
          class="form-control border-start-0"
          placeholder="Search project ID, contractor, district"
        />
      </div>

      <button class="btn btn-light position-relative">
        <i class="bi bi-bell"></i>
        <span
          class="position-absolute top-0 start-100 translate-middle p-1 bg-danger border border-light rounded-circle"
        ></span>
      </button>

      <div class="pm-avatar" style="background:#fde68a;color:#92400e;width:36px;height:36px;">
        {{ currentUser.initials }}
      </div>
    </div>
  </header>
</template>
