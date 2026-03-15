<script setup lang="ts">
defineProps<{
  loading: boolean
}>()

defineEmits<{
  confirm: []
  cancel: []
}>()
</script>

<template>
  <Teleport to="body">
    <div class="modal-overlay" @click.self="$emit('cancel')">
      <div class="modal-box">
        <h2>Checkout — Coming Soon</h2>
        <p>Full source packages (all .lua files, compiled .qplug, and chat history) will be available for purchase soon. For now, you can download the complete package for free.</p>
        <div class="modal-actions">
          <button class="btn-modal-cancel" @click="$emit('cancel')">Cancel</button>
          <button class="btn-modal-primary" :disabled="loading" @click="$emit('confirm')">
            {{ loading ? 'Downloading...' : 'Download Anyway' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
