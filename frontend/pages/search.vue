<script setup lang="ts">
interface SearchResult {
  type: 'page' | 'post'
  object_id: number
  locale: string
  title: string
  content: string
  url_path: string
  score: number
}

const route = useRoute()
const router = useRouter()
const config = useRuntimeConfig()
const apiBase = (import.meta.server ? config.apiBaseInternal : config.public.apiBase) as string
const { t } = useI18n()

const query = ref(String(route.query.q || ''))

const { data, pending } = await useFetch<{ results: SearchResult[] }>('/api/v1/search/', {
  key: () => `search:${route.query.q || ''}`,
  baseURL: apiBase,
  query: computed(() => ({ q: route.query.q || '' })),
})

const results = computed(() => data.value?.results || [])

function hrefFor(result: SearchResult): string {
  return result.type === 'post' ? `/post/${result.url_path}` : `/${result.url_path}`
}

function snippet(content: string): string {
  const clean = content.trim()
  return clean.length > 180 ? `${clean.slice(0, 180)}…` : clean
}

async function submitSearch() {
  await router.push({ path: '/search', query: { q: query.value.trim() } })
}

watch(
  () => route.query.q,
  (q) => {
    query.value = String(q || '')
  },
)

useSeoMeta({ title: () => (query.value ? `${t('publicSearch.title')}: ${query.value}` : t('publicSearch.title')) })
</script>

<template>
  <main class="mx-auto max-w-3xl px-6 py-12">
    <h1 class="text-3xl font-black">{{ $t('publicSearch.title') }}</h1>
    <form class="mt-4 flex gap-2" @submit.prevent="submitSearch">
      <input v-model="query" type="search" :placeholder="$t('publicSearch.placeholder')" class="bento-input flex-1" />
      <v-btn color="primary" type="submit">{{ $t('publicSearch.searchButton') }}</v-btn>
    </form>

    <div class="mt-8">
      <p v-if="pending" class="text-sm" style="color: var(--text-faint)">{{ $t('publicSearch.searching') }}</p>
      <p v-else-if="!route.query.q" class="text-sm" style="color: var(--text-faint)">
        {{ $t('publicSearch.enterTerm') }}
      </p>
      <p v-else-if="!results.length" class="text-sm" style="color: var(--text-faint)">
        {{ $t('publicSearch.noResultsFor', { q: route.query.q }) }}
      </p>
      <div v-else class="space-y-4">
        <p class="text-sm" style="color: var(--text-faint)">
          {{ $t('publicSearch.resultsFor', { n: results.length, q: route.query.q }) }}
        </p>
        <NuxtLink
          v-for="result in results"
          :key="`${result.type}-${result.object_id}-${result.locale}`"
          :to="hrefFor(result)"
          class="bento-tile block"
        >
          <span class="text-xs font-bold uppercase" style="color: var(--text-faint)">{{ $t(`publicSearch.type${result.type === 'post' ? 'Post' : 'Page'}`) }}</span>
          <h2 class="mt-1 text-lg font-bold">{{ result.title }}</h2>
          <p v-if="result.content" class="mt-1 text-sm" style="color: var(--text-secondary)">
            {{ snippet(result.content) }}
          </p>
        </NuxtLink>
      </div>
    </div>
  </main>
</template>
