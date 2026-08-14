<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

const { confirm } = useConfirmDialog()
const { t } = useI18n()

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

const uploading = ref(false)
const showTrash = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

const search = ref('')
// processing_status, not mime_type: django-filter's auto filterset does exact
// matches, and mime types are specific ("image/png", not "image") — a dropdown
// of every distinct mime type in the library would be far less useful than the
// small fixed set of processing states.
const statusFilter = ref<string | null>(null)

const { items, loading, loadingMore, hasMore, load, loadMore } = useInfiniteList<MediaRow>(() => {
  const params = new URLSearchParams({ trash: showTrash.value ? '1' : '0' })
  if (search.value) params.set('search', search.value)
  if (statusFilter.value) params.set('processing_status', statusFilter.value)
  return `/api/v1/media/?${params}`
})
const sentinel = useInfiniteScrollSentinel(loadMore)

const debouncedLoad = useDebounceFn(load, 300)
watch(search, debouncedLoad)
watch(statusFilter, load)

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
  const ok = await confirm({
    message: t('mediaAdmin.deleteConfirm', { filename: item.original_filename }),
    danger: true,
  })
  if (!ok) return
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
      <h1 class="text-2xl font-black">{{ $t('nav.media') }}</h1>
      <div class="flex items-center gap-3">
        <div class="bento-pill-group">
          <button class="bento-pill" :class="{ 'bento-pill--active': !showTrash }" @click="showTrash = false">
            {{ $t('mediaAdmin.library') }}
          </button>
          <button class="bento-pill" :class="{ 'bento-pill--active': showTrash }" @click="showTrash = true">{{ $t('mediaAdmin.trash') }}</button>
        </div>
        <input ref="fileInput" type="file" multiple class="hidden" @change="onFilesSelected" />
        <v-btn color="primary" :loading="uploading" @click="triggerUpload">
          <Icon name="solar:cloud-upload-bold-duotone" size="1.05rem" class="mr-1.5" />
          {{ $t('mediaAdmin.upload') }}
        </v-btn>
      </div>
    </div>

    <div class="mt-6 flex flex-wrap items-center gap-3">
      <v-text-field
        v-model="search"
        :placeholder="$t('mediaAdmin.searchPlaceholder')"
        hide-details
        density="compact"
        style="max-width: 18rem"
      >
        <template #prepend-inner><Icon name="solar:magnifer-bold-duotone" size="1.05rem" /></template>
      </v-text-field>
      <v-select
        v-model="statusFilter"
        :items="[
          { title: $t('mediaStatus.allStatuses'), value: null },
          { title: $t('mediaStatus.done'), value: 'done' },
          { title: $t('mediaStatus.pending'), value: 'pending' },
          { title: $t('mediaStatus.processing'), value: 'processing' },
          { title: $t('mediaStatus.failed'), value: 'failed' },
          { title: $t('mediaStatus.skipped'), value: 'skipped' },
        ]"
        hide-details
        density="compact"
        style="max-width: 12rem"
      />
    </div>

    <p v-if="loading" class="mt-4 text-sm" style="color: var(--text-faint)">{{ $t('common.loading') }}</p>
    <p v-else-if="!items.length" class="mt-4 text-sm" style="color: var(--text-faint)">
      {{ showTrash ? $t('mediaAdmin.trashEmpty') : search || statusFilter ? $t('mediaAdmin.noMediaMatches') : $t('mediaAdmin.noMediaYet') }}
    </p>
    <div v-else class="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-6">
      <div v-for="item in items" :key="item.id" class="bento-card overflow-hidden">
        <div class="flex aspect-square items-center justify-center" style="background: var(--surface-2)">
          <img
            v-if="isImage(item) && item.thumbnail_small"
            :src="item.thumbnail_small"
            :alt="item.original_filename"
            class="h-full w-full object-cover"
          />
          <Icon v-else name="solar:file-bold-duotone" size="2rem" style="color: var(--text-faint)" />
        </div>
        <div class="p-2">
          <div class="truncate text-xs font-semibold" :title="item.original_filename">
            {{ item.original_filename }}
          </div>
          <div class="mt-0.5 flex items-center justify-between text-xs" style="color: var(--text-faint)">
            <span>{{ prettySize(item.size_bytes) }}</span>
            <span v-if="item.processing_status !== 'done'">{{ $t(`mediaStatus.${item.processing_status}`) }}</span>
          </div>
          <div class="mt-1 flex justify-end">
            <button v-if="showTrash" class="bento-icon-btn bento-icon-btn--success" :title="$t('common.restore')" @click="restoreItem(item)">
              <Icon name="solar:undo-left-bold-duotone" size="1rem" />
            </button>
            <button v-else class="bento-icon-btn bento-icon-btn--danger" :title="$t('common.delete')" @click="removeItem(item)">
              <Icon name="solar:trash-bin-2-bold-duotone" size="1rem" />
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="items.length" ref="sentinel" class="flex justify-center py-4">
      <span v-if="loadingMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.loadingMore') }}</span>
      <span v-else-if="!hasMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.endOfList') }}</span>
    </div>
  </div>
</template>
