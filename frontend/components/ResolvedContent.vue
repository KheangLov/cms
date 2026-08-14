<script setup lang="ts">
// Shared by pages/index.vue (path="") and pages/[...slug].vue (path=joined
// segments) — CMS_BUILD_PROMPT.md §5.1's resolver doesn't care whether a path is
// empty (homepage) or nested, so neither does this component.
const props = defineProps<{ path: string }>()

const config = useRuntimeConfig()
const apiBase = (import.meta.server ? config.apiBaseInternal : config.public.apiBase) as string
const { locale, t } = useI18n()

// See [...slug].vue's original note: the explicit key matters because baseURL
// differs between server (apiBaseInternal) and client, which would otherwise
// break SSR/hydration payload matching.
const { data, error } = await useFetch<{ type: 'page' | 'post'; data: any }>('/api/v1/resolve/', {
  key: `resolve:${props.path}`,
  baseURL: apiBase,
  query: { path: props.path },
})

if (error.value) {
  throw createError({ statusCode: 404, statusMessage: t('resolvedContent.notFound') })
}

const resolved = computed(() => data.value?.data)
const isPost = computed(() => data.value?.type === 'post')

// Falls back to the first available translation (e.g. an untranslated km page
// still shows its en content) rather than rendering nothing.
function translation(loc = locale.value) {
  return resolved.value?.translations?.find((t: any) => t.locale === loc) || resolved.value?.translations?.[0]
}

// Category's own translations array works the same way — the base `name`
// field is just the canonical/admin-facing value, always English.
function categoryName(): string {
  const category = resolved.value?.category
  if (!category) return ''
  const match = category.translations?.find((tr: any) => tr.locale === locale.value)
  return match?.name || category.name
}

useSeoMeta({
  title: () => translation()?.meta_title || translation()?.title || t('resolvedContent.defaultTitle'),
  description: () => translation()?.meta_description || translation()?.excerpt || undefined,
})

// Background is full-bleed (behind the whole viewport width) while the content
// column stays constrained — "page background" and "page container" are two
// separate customizations, not one setting.
const CONTAINER_CLASSES: Record<string, string> = {
  narrow: 'max-w-xl',
  default: 'max-w-3xl',
  wide: 'max-w-5xl',
  full: 'max-w-none',
}
const containerClass = computed(() => CONTAINER_CLASSES[resolved.value?.container_width] || CONTAINER_CLASSES.default)

const backgroundStyle = computed(() => {
  const style: Record<string, string> = {}
  if (resolved.value?.background_color) style.background = resolved.value.background_color
  if (resolved.value?.background_image_url) {
    style.backgroundImage = `url(${resolved.value.background_image_url})`
    style.backgroundSize = 'cover'
    style.backgroundPosition = 'center'
    style.backgroundAttachment = 'fixed'
  }
  return style
})
</script>

<template>
  <div :style="backgroundStyle">
    <main class="mx-auto px-6 py-12" :class="containerClass">
      <template v-if="resolved">
        <header v-if="isPost" class="mb-8">
          <h1 class="text-3xl font-black">{{ translation()?.title }}</h1>
          <p v-if="resolved.category" class="mt-1 text-sm text-gray-500">{{ categoryName() }}</p>
        </header>
        <BlocksBlockRenderer :blocks="resolved.blocks || []" :locale="locale" />
        <CommentsSection :comments="resolved.comments || []" />
      </template>
    </main>
  </div>
</template>
