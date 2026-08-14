// Every admin list page was silently capped at DRF's page_size=20 — `results`
// was read but `next`/`count` were discarded, so anything past the first page
// was simply unreachable in the UI. This composable is the fix: `load()`
// fetches the first page (call it again to reset — e.g. on a filter change),
// `loadMore()` appends the next page. Pair with useInfiniteScrollSentinel to
// trigger loadMore() automatically.
export function useInfiniteList<T>(buildUrl: () => string) {
  const items = ref<T[]>([]) as Ref<T[]>
  const loading = ref(true)
  const loadingMore = ref(false)
  const nextUrl = ref<string | null>(null)

  async function load() {
    loading.value = true
    nextUrl.value = null
    try {
      const resp = await useAuthFetch<any>(buildUrl())
      if (Array.isArray(resp)) {
        items.value = resp
      } else {
        items.value = resp.results || []
        nextUrl.value = resp.next || null
      }
    } finally {
      loading.value = false
    }
  }

  async function loadMore() {
    if (!nextUrl.value || loadingMore.value) return
    loadingMore.value = true
    try {
      // DRF's `next` is a full absolute URL; useAuthFetch prepends its own
      // baseURL, so only the path+query survive the round trip.
      const parsed = new URL(nextUrl.value)
      const resp = await useAuthFetch<any>(parsed.pathname + parsed.search)
      const results = Array.isArray(resp) ? resp : resp.results || []
      items.value = [...items.value, ...results]
      nextUrl.value = Array.isArray(resp) ? null : resp.next || null
    } finally {
      loadingMore.value = false
    }
  }

  const hasMore = computed(() => !!nextUrl.value)

  return { items, loading, loadingMore, hasMore, load, loadMore }
}
