<script setup lang="ts">
defineProps<{
  subtitle: string
}>()
</script>

<template>
  <header>
    <h1>Q-SYS Plugin Generator</h1>
    <p>{{ subtitle }}</p>
  </header>
</template>
