<script setup lang="ts">
// WordPress-inspired "Latest Posts" block, with a manual-curation escape hatch.
// Unlike every other block component, this one fetches its own data (a list of
// posts) rather than just rendering block.props directly — every other block's
// content is self-contained JSON, but "which posts" is inherently a query
// against another entity.
interface Props {
  block: { id: number; props: Record<string, any> }
  locale?: string
}
const props = defineProps<Props>()
const config = useRuntimeConfig()
const apiBase = (import.meta.server ? config.apiBaseInternal : config.public.apiBase) as string

function t(field: string): string {
  const value = props.block.props[field]
  if (value && typeof value === 'object') {
    return value[props.locale || 'en'] ?? value.en ?? ''
  }
  return value ?? ''
}

const categorySlug = computed(() => (props.block.props.categorySlug || '').trim())
const count = computed(() => {
  const n = Number(props.block.props.count)
  return Number.isFinite(n) && n > 0 ? Math.min(n, 12) : 3
})
// Manual curation, set via the block's advanced JSON editor (props.postIds), the
// same "list -> raw JSON" escape hatch every other structured field already uses
// (see Swiper's `slides`) — no bespoke picker UI, consistent with the rest of the
// prop schema system.
const postIds = computed<number[]>(() => {
  const raw = props.block.props.postIds
  return Array.isArray(raw) ? raw.map(Number).filter((n) => Number.isFinite(n)) : []
})

// The `category` filterset field matches by id, not slug, so a human-typed slug
// needs one resolution lookup before it can filter the posts query.
const { data: categories } = await useFetch<{ results: any[] } | any[]>('/api/v1/categories/', {
  key: `posts-block-categories-${props.block.id}`,
  baseURL: apiBase,
})
const categoryId = computed(() => {
  if (!categorySlug.value) return null
  const list = Array.isArray(categories.value) ? categories.value : categories.value?.results || []
  return list.find((c: any) => c.slug === categorySlug.value)?.id ?? null
})

const query = computed(() => {
  if (postIds.value.length) return {}
  const q: Record<string, any> = { status: 'published', ordering: '-published_at' }
  if (categoryId.value) q.category = categoryId.value
  return q
})

const { data } = await useFetch<{ results: any[] } | any[]>('/api/v1/posts/', {
  key: `posts-block-${props.block.id}`,
  baseURL: apiBase,
  query,
})

const posts = computed(() => {
  const list = Array.isArray(data.value) ? data.value : data.value?.results || []
  if (postIds.value.length) {
    // Preserve the curated order — the API has no guarantee of matching it.
    const byId = new Map(list.map((p: any) => [p.id, p]))
    return postIds.value.map((id) => byId.get(id)).filter(Boolean)
  }
  return list.slice(0, count.value)
})

function titleFor(post: any): string {
  return post.translations?.find((tr: any) => tr.locale === (props.locale || 'en'))?.title || post.slug
}
function excerptFor(post: any): string {
  return post.translations?.find((tr: any) => tr.locale === (props.locale || 'en'))?.excerpt || ''
}
</script>

<template>
  <section class="px-6 py-8">
    <h2 v-if="t('heading')" class="mb-4 text-2xl font-black">{{ t('heading') }}</h2>
    <p v-if="!posts.length" class="text-sm" style="color: var(--text-faint)">{{ $t('publicPosts.noPostsToShow') }}</p>
    <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <NuxtLink
        v-for="post in posts"
        :key="post.id"
        :to="`/post/${post.slug}`"
        class="bento-tile block p-4"
      >
        <h3 class="font-bold">{{ titleFor(post) }}</h3>
        <p v-if="excerptFor(post)" class="mt-1 text-sm" style="color: var(--text-secondary)">
          {{ excerptFor(post) }}
        </p>
      </NuxtLink>
    </div>
  </section>
</template>
