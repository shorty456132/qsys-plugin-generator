<script setup lang="ts">
import { ref, computed } from 'vue'
import FileDropZone from './FileDropZone.vue'

const props = defineProps<{
  mode: 'create' | 'modify'
  showBack?: boolean
}>()

defineEmits<{
  generate: [formData: FormData]
  cancel: []
}>()

const pluginName = defineModel<string>('pluginName', { required: true })

const description = ref('')
const protocol = ref('TCP')
const connection = ref('')
const apiDocUrl = ref('')
const apiDocFiles = ref<File[]>([])
const pluginFiles = ref<File[]>([])
const webSearch = ref(false)
const activeTab = ref<'url' | 'file'>('url')
const phase2Open = ref(false)

// In modify mode, phase2 is always open
if (props.mode === 'modify') {
  phase2Open.value = true
}

const canContinue = computed(() =>
  pluginName.value.trim().length > 0 && description.value.trim().length > 0
)

function openPhase2() {
  if (phase2Open.value) return
  phase2Open.value = true
}

function onSubmit(emit: (event: 'generate', formData: FormData) => void) {
  const fd = new FormData()
  fd.append('mode', props.mode)
  fd.append('plugin_name', pluginName.value.trim())
  fd.append('description', description.value.trim())

  if (props.mode === 'modify') {
    for (const f of pluginFiles.value) {
      fd.append('plugin_files', f)
    }
  } else {
    fd.append('protocol', protocol.value)
    fd.append('connection', connection.value.trim())
  }

  if (webSearch.value) {
    fd.append('web_search', 'on')
  }

  if (activeTab.value === 'url') {
    fd.append('api_doc_url', apiDocUrl.value.trim())
  } else if (apiDocFiles.value.length > 0) {
    fd.append('api_doc_file', apiDocFiles.value[0])
  }

  emit('generate', fd)
}

const descriptionLabel = computed(() =>
  props.mode === 'modify' ? 'Modification Description' : 'Plugin Description'
)

const descriptionPlaceholder = computed(() =>
  props.mode === 'modify'
    ? 'Describe what changes you want to make to this plugin...'
    : "Describe what the plugin does and what device it controls. E.g. 'Control a Sony projector — power, input select, and volume over TCP.'"
)
</script>

<template>
  <form @submit.prevent="onSubmit($emit)">
    <button v-if="showBack" type="button" class="btn-back" @click="$emit('cancel')">
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <path d="M11 7H3M6.5 3.5L3 7l3.5 3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      Back
    </button>

    <div class="form-group">
      <label for="pluginName">Plugin Name</label>
      <input
        id="pluginName"
        v-model="pluginName"
        type="text"
        placeholder="e.g. Sony VPL Projector"
        required
      >
    </div>

    <!-- Plugin file upload (modify mode only) -->
    <div v-if="mode === 'modify'" class="form-group">
      <label>Existing Plugin Files</label>
      <FileDropZone
        v-model="pluginFiles"
        accept=".lua,.qplug,.zip"
        :multiple="true"
        label="Drop plugin files or"
        hint=".lua · .qplug · .zip"
      />
    </div>

    <div class="form-group">
      <label for="description">{{ descriptionLabel }}</label>
      <textarea
        id="description"
        v-model="description"
        class="description-textarea"
        :placeholder="descriptionPlaceholder"
        required
      ></textarea>
    </div>

    <!-- Continue button (create mode only) -->
    <button
      v-if="mode === 'create' && !phase2Open"
      type="button"
      class="btn-continue"
      :disabled="!canContinue"
      @click="openPhase2"
    >
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <path d="M3 7h8M7.5 3.5L11 7l-3.5 3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      Continue
    </button>

    <!-- Phase 2 -->
    <div class="phase2" :class="{ revealed: phase2Open }">
      <hr class="phase-divider">

      <!-- Protocol + Connection (create mode only) -->
      <div v-if="mode === 'create'" class="row-2">
        <div class="form-group" style="margin-bottom:0">
          <label for="protocol">Protocol</label>
          <select id="protocol" v-model="protocol">
            <option value="TCP">TCP</option>
            <option value="UDP">UDP</option>
            <option value="Serial">Serial</option>
            <option value="HTTP">HTTP</option>
            <option value="SSH">SSH</option>
            <option value="None">None</option>
          </select>
        </div>

        <div class="form-group" style="margin-bottom:0">
          <label for="connection">Connection Details</label>
          <input
            id="connection"
            v-model="connection"
            type="text"
            placeholder="Port, baud rate, default IP..."
          >
        </div>
      </div>

      <!-- API Doc -->
      <div class="form-group">
        <label>
          API / Protocol Document
          <span style="font-weight:400;color:#555;text-transform:none;letter-spacing:0">(optional)</span>
        </label>

        <div class="tab-bar">
          <button
            type="button"
            class="tab-btn"
            :class="{ active: activeTab === 'url' }"
            @click="activeTab = 'url'"
          >URL</button>
          <button
            type="button"
            class="tab-btn"
            :class="{ active: activeTab === 'file' }"
            @click="activeTab = 'file'"
          >File</button>
        </div>

        <div v-if="activeTab === 'url'">
          <input
            v-model="apiDocUrl"
            type="text"
            placeholder="https://manufacturer.com/protocol-guide.pdf"
          >
        </div>

        <div v-if="activeTab === 'file'">
          <FileDropZone
            v-model="apiDocFiles"
            accept=".pdf,.txt,.md,.json,.csv,.xml"
            :multiple="false"
            label="Drop a file here or"
            hint=".pdf · .txt · .md · .json · .csv · .xml"
          />
        </div>
      </div>

      <!-- Web search toggle -->
      <div class="form-group" style="margin-bottom:16px">
        <label class="checkbox-label">
          <input v-model="webSearch" type="checkbox">
          Search the web for device protocol documentation
        </label>
      </div>

      <button type="submit" class="btn-generate">Generate Plugin</button>
    </div>
  </form>
</template>
