<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  role: 'user' | 'assistant'
  content: string
}>()

function stripCodeBlocks(text: string): string {
  return text.replace(/```[\s\S]*?```/g, '').replace(/\n{3,}/g, '\n\n').trim()
}

const displayContent = computed(() =>
  props.role === 'assistant' ? stripCodeBlocks(props.content) : props.content
)

const label = computed(() => (props.role === 'user' ? 'You' : 'Assistant'))
</script>

<template>
  <div class="chat-msg" :class="role">
    <div class="chat-msg-label">{{ label }}</div>
    <div>{{ displayContent }}</div>
  </div>
</template>
