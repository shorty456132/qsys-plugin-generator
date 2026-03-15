<script setup lang="ts">
import { ref, computed } from 'vue'
import AppHeader from './components/AppHeader.vue'
import ModeSelector from './components/ModeSelector.vue'
import PluginForm from './components/PluginForm.vue'
import ChatPanel from './components/ChatPanel.vue'
import CheckoutModal from './components/CheckoutModal.vue'
import LoadingSpinner from './components/LoadingSpinner.vue'
import { useConversation } from './composables/useConversation'

type AppPhase = 'select' | 'form' | 'chat'

const phase = ref<AppPhase>('select')
const selectedMode = ref<'create' | 'modify'>('create')
const pluginName = ref('')
const showCheckout = ref(false)
const checkoutLoading = ref(false)

const conversation = useConversation()

const subtitle = computed(() => {
  if (selectedMode.value === 'modify' && phase.value !== 'select') {
    return 'Upload your plugin and describe the changes you need.'
  }
  return 'Describe your plugin and let Claude scaffold the Lua files.'
})

const isChatActive = computed(() => phase.value === 'chat')

function onModeSelect(mode: 'create' | 'modify') {
  selectedMode.value = mode
  phase.value = 'form'
}

async function onGenerate(formData: FormData) {
  await conversation.generate(formData)
  if (conversation.conversationId.value) {
    phase.value = 'chat'
  }
}

async function onSendReply(text: string) {
  await conversation.reply(text)
}

async function onTest() {
  await conversation.downloadTest(pluginName.value)
}

function onComplete() {
  showCheckout.value = true
}

async function onCheckoutConfirm() {
  checkoutLoading.value = true
  const success = await conversation.complete(pluginName.value)
  checkoutLoading.value = false
  showCheckout.value = false
  if (success) {
    await onStartOver()
  }
}

async function onStartOver() {
  await conversation.reset()
  phase.value = 'select'
  pluginName.value = ''
  showCheckout.value = false
  checkoutLoading.value = false
}
</script>

<template>
  <AppHeader :subtitle="subtitle" />

  <div class="page-layout" :class="{ 'chat-active': isChatActive }">
    <div class="card">
      <!-- Mode Selection -->
      <ModeSelector v-if="phase === 'select'" @select="onModeSelect" />

      <!-- Plugin Form -->
      <PluginForm
        v-if="phase === 'form' || phase === 'chat'"
        v-show="phase === 'form' || phase === 'chat'"
        v-model:plugin-name="pluginName"
        :mode="selectedMode"
        @generate="onGenerate"
      />

      <LoadingSpinner
        v-if="conversation.loading.value && phase === 'form'"
        message="Generating plugin files — this may take a moment..."
      />

      <div v-if="conversation.error.value && phase !== 'chat'" class="error-msg">
        {{ conversation.error.value }}
      </div>

      <button
        v-if="phase === 'chat'"
        type="button"
        class="btn-new-plugin"
        @click="onStartOver"
      >+ Start Over</button>
    </div>

    <!-- Chat Panel -->
    <ChatPanel
      v-if="isChatActive"
      :messages="conversation.messages.value"
      :loading="conversation.loading.value"
      :has-files="conversation.hasFiles.value"
      :error="conversation.error.value"
      @send="onSendReply"
      @test="onTest"
      @complete="onComplete"
      @copy=""
      @start-over="onStartOver"
    />
  </div>

  <!-- Checkout Modal -->
  <CheckoutModal
    v-if="showCheckout"
    :loading="checkoutLoading"
    @confirm="onCheckoutConfirm"
    @cancel="showCheckout = false"
  />
</template>
