<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

interface PageRow {
  id: number
  slug: string
  status: string
  translations: Array<{ locale: string; title: string }>
}

const pages = ref<PageRow[]>([])
const loading = ref(true)
const creating = ref(false)
const newSlug = ref('')
const pageTypes = ref<Array<{ id: number; name: string }>>([])
const newPageType = ref<number | null>(null)
const router = useRouter()

async function load() {
  loading.value = true
  const resp = await useAuthFetch<{ results: PageRow[] } | PageRow[]>('/api/v1/pages/?trash=0')
  pages.value = Array.isArray(resp) ? resp : resp.results
  loading.value = false
}

async function loadPageTypes() {
  const resp = await useAuthFetch<{ results: any[] } | any[]>('/api/v1/page-types/')
  pageTypes.value = Array.isArray(resp) ? resp : resp.results
}

function titleFor(page: PageRow): string {
  return page.translations.find((t) => t.locale === 'en')?.title || page.slug
}

async function createPage() {
  if (!newSlug.value || !newPageType.value) return
  const created = await useAuthFetch<PageRow>('/api/v1/pages/', {
    method: 'POST',
    body: { slug: newSlug.value, page_type: newPageType.value, translations: [{ locale: 'en', title: newSlug.value }] },
  })
  creating.value = false
  newSlug.value = ''
  await router.push(`/admin/pages/${created.id}`)
}

async function removePage(page: PageRow) {
  if (!confirm(`Delete "${titleFor(page)}"? This can be restored later from the trash.`)) return
  await useAuthFetch(`/api/v1/pages/${page.id}/`, { method: 'DELETE' })
  pages.value = pages.value.filter((p) => p.id !== page.id)
}

onMounted(() => {
  load()
  loadPageTypes()
})

useSeoMeta({ title: 'Pages — CMS Admin' })
</script>

<template>
  <div>
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-black">Pages</h1>
      <v-btn color="primary" @click="creating = true">New page</v-btn>
    </div>

    <div v-if="creating" class="mt-4 flex flex-wrap items-end gap-3 rounded-lg border p-4" style="border-color: var(--border); background: var(--surface)">
      <v-text-field v-model="newSlug" label="Slug" hide-details density="compact" style="max-width: 16rem" />
      <v-select
        v-model="newPageType"
        :items="pageTypes"
        item-title="name"
        item-value="id"
        label="Page type"
        hide-details
        density="compact"
        style="max-width: 14rem"
      />
      <v-btn color="primary" @click="createPage">Create</v-btn>
      <v-btn variant="text" @click="creating = false">Cancel</v-btn>
    </div>

    <p v-if="loading" class="mt-6 text-sm" style="color: var(--text-faint)">Loading…</p>
    <ul v-else class="mt-6 divide-y rounded-lg border" style="border-color: var(--border); background: var(--surface)">
      <li v-if="!pages.length" class="px-4 py-6 text-sm" style="color: var(--text-faint)">No pages yet.</li>
      <li v-for="page in pages" :key="page.id" class="flex items-center justify-between px-4 py-3">
        <div>
          <div class="font-semibold">{{ titleFor(page) }}</div>
          <div class="text-xs" style="color: var(--text-faint)">/{{ page.slug }} — {{ page.status }}</div>
        </div>
        <div class="flex items-center gap-3">
          <NuxtLink :to="`/admin/pages/${page.id}`" class="text-sm font-bold text-primary"> Edit blocks → </NuxtLink>
          <button class="text-xs" style="color: var(--error)" @click="removePage(page)">Delete</button>
        </div>
      </li>
    </ul>
  </div>
</template>
