<script setup lang="ts">
// Cmd/Ctrl+K global search across published Pages/Posts, backed by the
// Elasticsearch pipeline in apps/search (already indexes on every save via
// signals — this component is the only piece that was actually missing).
interface SearchResult {
  type: 'page' | 'post'
  object_id: number
  locale: string
  title: string
  url_path: string
  score: number
}

const open = ref(false)
const query = ref('')
const results = ref<SearchResult[]>([])
const loading = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)
const router = useRouter()

async function runSearch() {
  const q = query.value.trim()
  if (!q) {
    results.value = []
    return
  }
  loading.value = true
  try {
    const resp = await useAuthFetch<{ results: SearchResult[] }>(`/api/v1/search/?q=${encodeURIComponent(q)}`)
    results.value = resp.results
  } finally {
    loading.value = false
  }
}

watch(query, useDebounceFn(runSearch, 250))

function openPalette() {
  open.value = true
  query.value = ''
  results.value = []
  nextTick(() => inputRef.value?.focus())
}

function goTo(result: SearchResult) {
  open.value = false
  router.push(`/admin/${result.type}s/${result.object_id}`)
}

function iconFor(type: string): string {
  return type === 'post' ? 'solar:notes-bold-duotone' : 'solar:document-2-bold-duotone'
}

function onKeydown(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    open.value ? (open.value = false) : openPalette()
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))

defineExpose({ openPalette })
</script>

<template>
  <v-dialog v-model="open" max-width="560" scrim="black" :opacity="0.6">
    <div class="bento-card overflow-hidden p-0">
      <div class="flex items-center gap-2 border-b px-4 py-3" style="border-color: var(--border)">
        <Icon name="solar:magnifer-bold-duotone" size="1.1rem" style="color: var(--text-faint)" />
        <input
          ref="inputRef"
          v-model="query"
          type="text"
          :placeholder="$t('search.placeholder')"
          class="flex-1 bg-transparent text-sm outline-none"
          @keydown.esc="open = false"
        />
        <kbd class="rounded px-1.5 py-0.5 text-[0.65rem]" style="background: var(--surface-2); color: var(--text-faint)">Esc</kbd>
      </div>

      <div class="max-h-96 overflow-y-auto">
        <p v-if="loading" class="px-4 py-6 text-center text-sm" style="color: var(--text-faint)">{{ $t('search.searching') }}</p>
        <p v-else-if="query.trim() && !results.length" class="px-4 py-6 text-center text-sm" style="color: var(--text-faint)">
          {{ $t('search.noResultsFor', { query }) }}
        </p>
        <p v-else-if="!query.trim()" class="px-4 py-6 text-center text-sm" style="color: var(--text-faint)">
          {{ $t('search.hint') }}
        </p>
        <button
          v-for="result in results"
          :key="`${result.type}-${result.object_id}-${result.locale}`"
          class="bento-row w-full text-left"
          @click="goTo(result)"
        >
          <span class="bento-row__icon"><Icon :name="iconFor(result.type)" /></span>
          <div class="bento-row__body">
            <div class="font-semibold">{{ result.title }}</div>
            <div class="text-xs capitalize" style="color: var(--text-faint)">{{ result.type }} — /{{ result.url_path }}</div>
          </div>
        </button>
      </div>
    </div>
  </v-dialog>
</template>
