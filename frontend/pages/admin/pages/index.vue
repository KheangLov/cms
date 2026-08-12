<script setup lang="ts">
interface PageRow {
  id: number
  slug: string
  status: string
  translations: Array<{ locale: string; title: string }>
}

const auth = useAuthStore()
const pages = ref<PageRow[]>([])
const loading = ref(true)
const { notifications, connect, disconnect } = useNotifications()

async function load() {
  loading.value = true
  const resp = await useAuthFetch<{ results: PageRow[] } | PageRow[]>('/api/v1/pages/')
  pages.value = Array.isArray(resp) ? resp : resp.results
  loading.value = false
}

function titleFor(page: PageRow): string {
  return page.translations.find((t) => t.locale === 'en')?.title || page.slug
}

onMounted(() => {
  load()
  connect()
})
onUnmounted(disconnect)

useSeoMeta({ title: 'Pages — CMS Admin' })
</script>

<template>
  <div class="mx-auto max-w-3xl px-6 py-10">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-black">Pages</h1>
      <span v-if="auth.user" class="text-sm text-gray-500">{{ auth.user.email }}</span>
    </div>

    <ul v-if="notifications.length" class="mt-4 space-y-1">
      <li
        v-for="(n, i) in notifications"
        :key="i"
        class="rounded border border-primary/30 bg-primary/5 px-3 py-2 text-sm"
      >
        {{ n.event }} — {{ JSON.stringify(n) }}
      </li>
    </ul>

    <p v-if="loading" class="mt-6 text-sm text-gray-400">Loading…</p>
    <ul v-else class="mt-6 divide-y rounded border">
      <li v-for="page in pages" :key="page.id" class="flex items-center justify-between px-4 py-3">
        <div>
          <div class="font-semibold">{{ titleFor(page) }}</div>
          <div class="text-xs text-gray-400">/{{ page.slug }} — {{ page.status }}</div>
        </div>
        <NuxtLink :to="`/admin/pages/${page.id}`" class="text-sm font-bold text-primary">
          Edit blocks →
        </NuxtLink>
      </li>
    </ul>
  </div>
</template>
