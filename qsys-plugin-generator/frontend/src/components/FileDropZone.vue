<script setup lang="ts">
import { ref } from 'vue'

const files = defineModel<File[]>({ required: true })

defineProps<{
  accept: string
  multiple?: boolean
  label: string
  hint: string
}>()

const dragover = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

function onDrop(e: DragEvent) {
  dragover.value = false
  if (e.dataTransfer?.files.length) {
    addFiles(e.dataTransfer.files)
  }
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.length) {
    addFiles(input.files)
  }
}

function addFiles(fileList: FileList) {
  const newFiles = [...files.value]
  for (const f of fileList) {
    newFiles.push(f)
  }
  files.value = newFiles
  if (fileInput.value) fileInput.value.value = ''
}

function removeFile(index: number) {
  const newFiles = [...files.value]
  newFiles.splice(index, 1)
  files.value = newFiles
}

function clearAll() {
  files.value = []
}
</script>

<template>
  <div>
    <div
      class="file-drop"
      :class="{ dragover }"
      @dragenter.prevent="dragover = true"
      @dragover.prevent="dragover = true"
      @dragleave.prevent="dragover = false"
      @drop.prevent="onDrop"
    >
      <input
        ref="fileInput"
        type="file"
        :accept="accept"
        :multiple="multiple"
        @change="onFileChange"
      >
      <div class="file-drop-icon">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="12" y1="18" x2="12" y2="12"/>
          <line x1="9" y1="15" x2="15" y2="15"/>
        </svg>
      </div>
      <p>{{ label }} <span>browse</span></p>
      <p class="file-hint">{{ hint }}</p>
    </div>

    <div v-if="files.length > 0" class="plugin-file-list">
      <div v-for="(file, i) in files" :key="i" class="plugin-file-item">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
        <span>{{ file.name }}</span>
        <button type="button" style="margin-left:auto;background:none;border:none;color:#555;cursor:pointer" @click="removeFile(i)">&#10005;</button>
      </div>
      <button v-if="multiple && files.length > 1" type="button" class="btn-clear-files" @click="clearAll">
        Clear all files
      </button>
    </div>
  </div>
</template>
