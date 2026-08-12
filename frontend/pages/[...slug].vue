<script setup lang="ts">
// CMS_BUILD_PROMPT.md §5.1 — the single resolver endpoint means this route never
// has to guess whether a URL is a Page or a Post; the backend already decided.
const route = useRoute()
const config = useRuntimeConfig()
const apiBase = (import.meta.server ? config.apiBaseInternal : config.public.apiBase) as string

const path = Array.isArray(route.params.slug) ? route.params.slug.join('/') : String(route.params.slug || '')

const { data, error } = await useFetch<{ type: 'page' | 'post'; data: any }>('/api/v1/resolve/', {
  baseURL: apiBase,
  query: { path },
})

if (error.value) {
  throw createError({ statusCode: 404, statusMessage: 'Not found' })
}

const resolved = computed(() => data.value?.data)
const isPost = computed(() => data.value?.type === 'post')

function translation(locale = 'en') {
  return resolved.value?.translations?.find((t: any) => t.locale === locale) || resolved.value?.translations?.[0]
}

useSeoMeta({
  title: () => translation()?.meta_title || translation()?.title || 'CMS Platform',
  description: () => translation()?.meta_description || translation()?.excerpt || undefined,
})
</script>

<template>
  <main class="mx-auto max-w-3xl px-6 py-12">
    <template v-if="resolved">
      <header v-if="isPost" class="mb-8">
        <h1 class="text-3xl font-black">{{ translation()?.title }}</h1>
        <p v-if="resolved.category" class="mt-1 text-sm text-gray-500">{{ resolved.category.name }}</p>
      </header>
      <BlocksBlockRenderer :blocks="resolved.blocks || []" locale="en" />
    </template>
  </main>
</template>
