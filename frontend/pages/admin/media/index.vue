<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

interface MediaRow {
  id: number
  file: string
  thumbnail_small: string | null
  original_filename: string
  mime_type: string
  size_bytes: number
  processing_status: string
  is_deleted: boolean
}

const items = ref<MediaRow[]>([])
const loading = ref(true)
const uploading = ref(false)
const showTrash = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

async function load() {
  loading.value = true
  const path = showTrash.value ? '/api/v1/media/?trash=1' : '/api/v1/media/?trash=0'
  const resp = await useAuthFetch<{ results: MediaRow[] } | MediaRow[]>(path)
  items.value = Array.isArray(resp) ? resp : resp.results
  loading.value = false
}

function isImage(m: MediaRow): boolean {
  return m.mime_type.startsWith('image/')
}

function prettySize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function triggerUpload() {
  fileInput.value?.click()
}

async function onFilesSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const files = input.files
  if (!files?.length) return
  uploading.value = true
  for (const file of Array.from(files)) {
    const formData = new FormData()
    formData.append('file', file)
    await useAuthFetch('/api/v1/media/', { method: 'POST', body: formData })
  }
  input.value = ''
  uploading.value = false
  await load()
}

async function removeItem(item: MediaRow) {
  if (!confirm(`Delete "${item.original_filename}"? This can be restored from the trash.`)) return
  await useAuthFetch(`/api/v1/media/${item.id}/`, { method: 'DELETE' })
  await load()
}

async function restoreItem(item: MediaRow) {
  await useAuthFetch(`/api/v1/media/${item.id}/restore/`, { method: 'POST' })
  await load()
}

watch(showTrash, load)
onMounted(load)

useSeoMeta({ title: 'Media — CMS Admin' })
</script>

<template>
  <div>
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-black">Media</h1>
      <div class="flex items-center gap-4">
        <button class="text-sm font-semibold" style="color: var(--text-secondary)" @click="showTrash = !showTrash">
          {{ showTrash ? 'Back to library' : 'Trash' }}
        </button>
        <input ref="fileInput" type="file" multiple class="hidden" @change="onFilesSelected" />
        <v-btn color="primary" :loading="uploading" @click="triggerUpload">Upload</v-btn>
      </div>
    </div>

    <p v-if="loading" class="mt-6 text-sm" style="color: var(--text-faint)">Loading…</p>
    <p v-else-if="!items.length" class="mt-6 text-sm" style="color: var(--text-faint)">
      {{ showTrash ? 'Trash is empty.' : 'No media yet — upload something.' }}
    </p>
    <div v-else class="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-6">
      <div
        v-for="item in items"
        :key="item.id"
        class="overflow-hidden rounded-lg border"
        style="border-color: var(--border); background: var(--surface)"
      >
        <div class="flex aspect-square items-center justify-center" style="background: var(--surface-2)">
          <img
            v-if="isImage(item) && item.thumbnail_small"
            :src="item.thumbnail_small"
            :alt="item.original_filename"
            class="h-full w-full object-cover"
          />
          <span v-else class="text-xs" style="color: var(--text-faint)">{{ item.mime_type }}</span>
        </div>
        <div class="p-2">
          <div class="truncate text-xs font-semibold" :title="item.original_filename">
            {{ item.original_filename }}
          </div>
          <div class="mt-0.5 flex items-center justify-between text-xs" style="color: var(--text-faint)">
            <span>{{ prettySize(item.size_bytes) }}</span>
            <span v-if="item.processing_status !== 'done'">{{ item.processing_status }}</span>
          </div>
          <div class="mt-1 flex justify-end gap-2">
            <button v-if="showTrash" class="text-xs font-semibold" style="color: var(--success)" @click="restoreItem(item)">
              Restore
            </button>
            <button v-else class="text-xs" style="color: var(--error)" @click="removeItem(item)">Delete</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
