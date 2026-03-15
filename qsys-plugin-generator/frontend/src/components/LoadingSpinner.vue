<script setup lang="ts">
defineProps<{
  message: string
}>()
</script>

<template>
  <div class="spinner">
    <div class="spinner-ring"></div>
    <span>{{ message }}</span>
  </div>
</template>
