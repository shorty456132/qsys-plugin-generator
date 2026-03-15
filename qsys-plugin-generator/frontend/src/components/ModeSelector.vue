<script setup lang="ts">
defineEmits<{
  select: [mode: 'create' | 'modify']
}>()
</script>

<template>
  <div class="mode-selector">
    <div class="mode-card" @click="$emit('select', 'create')">
      <div class="mode-card-icon">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 5v14M5 12h14"/>
        </svg>
      </div>
      <h3>Create New Plugin</h3>
      <p>Scaffold a complete plugin from scratch</p>
    </div>
    <div class="mode-card" @click="$emit('select', 'modify')">
      <div class="mode-card-icon">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
        </svg>
      </div>
      <h3>Modify Existing Plugin</h3>
      <p>Upload a plugin and make changes</p>
    </div>
  </div>
</template>
