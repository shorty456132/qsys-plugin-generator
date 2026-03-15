import { ref, computed } from 'vue'
import {
  generate as apiGenerate,
  reply as apiReply,
  downloadPlugin,
  completePlugin,
  deleteConversation,
  triggerDownload,
  safeName,
} from '@/api/client'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export function useConversation() {
  const conversationId = ref<string | null>(null)
  const messages = ref<ChatMessage[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const hasFiles = computed(() =>
    messages.value.some(
      (m) => m.role === 'assistant' && /```(?:\w+\s+)?filename:/m.test(m.content)
    )
  )

  function clearError() {
    error.value = null
  }

  async function generate(formData: FormData) {
    loading.value = true
    error.value = null
    messages.value = []
    conversationId.value = null

    try {
      const data = await apiGenerate(formData)
      conversationId.value = data.conversation_id
      messages.value.push({ role: 'assistant', content: data.result })
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'An unexpected error occurred.'
    } finally {
      loading.value = false
    }
  }

  async function reply(text: string) {
    if (!text || !conversationId.value) return

    messages.value.push({ role: 'user', content: text })
    loading.value = true
    error.value = null

    try {
      const data = await apiReply(conversationId.value, text)
      messages.value.push({ role: 'assistant', content: data.result })
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'An unexpected error occurred.'
    } finally {
      loading.value = false
    }
  }

  async function downloadTest(pluginName: string) {
    if (!conversationId.value) return
    error.value = null

    try {
      const blob = await downloadPlugin(conversationId.value, pluginName)
      triggerDownload(blob, safeName(pluginName) + '.qplug')
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Download failed.'
    }
  }

  async function complete(pluginName: string): Promise<boolean> {
    if (!conversationId.value) return false
    error.value = null

    try {
      const blob = await completePlugin(conversationId.value, pluginName)
      triggerDownload(blob, safeName(pluginName) + '-complete.zip')
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Download failed.'
      return false
    }
  }

  async function reset() {
    if (conversationId.value) {
      await deleteConversation(conversationId.value)
    }
    conversationId.value = null
    messages.value = []
    loading.value = false
    error.value = null
  }

  return {
    conversationId,
    messages,
    loading,
    error,
    hasFiles,
    clearError,
    generate,
    reply,
    downloadTest,
    complete,
    reset,
  }
}
