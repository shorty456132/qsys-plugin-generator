<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import ChatMessage from './ChatMessage.vue'
import LoadingSpinner from './LoadingSpinner.vue'
import type { ChatMessage as ChatMessageType } from '@/composables/useConversation'

const props = defineProps<{
  messages: ChatMessageType[]
  loading: boolean
  hasFiles: boolean
  error: string | null
}>()

defineEmits<{
  send: [text: string]
  test: []
  complete: []
  copy: []
  'start-over': []
}>()

const replyText = ref('')
const chatHistoryEl = ref<HTMLElement | null>(null)
const copyLabel = ref('Copy')

function onSend(emit: (event: 'send', text: string) => void) {
  const text = replyText.value.trim()
  if (!text) return
  replyText.value = ''
  emit('send', text)
}

function onKeydown(e: KeyboardEvent, emit: (event: 'send', text: string) => void) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    onSend(emit)
  }
}

function onCopy(emit: (event: 'copy') => void) {
  const assistantMsgs = props.messages.filter((m) => m.role === 'assistant')
  if (assistantMsgs.length === 0) return
  const lastContent = assistantMsgs[assistantMsgs.length - 1].content
  const stripped = lastContent.replace(/```[\s\S]*?```/g, '').replace(/\n{3,}/g, '\n\n').trim()
  navigator.clipboard.writeText(stripped).then(() => {
    copyLabel.value = 'Copied!'
    setTimeout(() => { copyLabel.value = 'Copy' }, 2000)
  })
  emit('copy')
}

watch(
  () => props.messages.length,
  async () => {
    await nextTick()
    if (chatHistoryEl.value) {
      const el = chatHistoryEl.value
      el.scrollTop = el.scrollHeight
    }
  }
)
</script>

<template>
  <div class="chat-panel">
    <div class="output-section">
      <div class="output-header">
        <span>Generated Output</span>
        <div class="output-header-buttons">
          <button v-if="hasFiles" class="btn-test" :disabled="loading" @click="$emit('test')">
            Test it out
          </button>
          <button v-if="hasFiles" class="btn-complete" :disabled="loading" @click="$emit('complete')">
            Complete
          </button>
          <button
            class="btn-copy"
            :class="{ copied: copyLabel === 'Copied!' }"
            @click="onCopy($emit)"
          >
            {{ copyLabel }}
          </button>
        </div>
      </div>

      <div ref="chatHistoryEl" class="chat-history">
        <ChatMessage
          v-for="(msg, i) in messages"
          :key="i"
          :role="msg.role"
          :content="msg.content"
        />
        <LoadingSpinner v-if="loading" message="Generating response..." />
      </div>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>

    <div class="reply-section">
      <div class="reply-row">
        <textarea
          v-model="replyText"
          class="reply-input"
          placeholder="Type your reply..."
          rows="1"
          :disabled="loading"
          @keydown="onKeydown($event, $emit)"
        ></textarea>
        <button
          class="btn-send"
          :disabled="loading || !replyText.trim()"
          @click="onSend($emit)"
        >Send</button>
      </div>
    </div>
  </div>
</template>
