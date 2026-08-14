<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

const { confirm } = useConfirmDialog()
const { t, locale } = useI18n()

interface PageRow {
  id: number
  slug: string
  status: string
  full_path: string
  translations: Array<{ locale: string; title: string }>
}

const creating = ref(false)
const newSlug = ref('')
const pageTypes = ref<Array<{ id: number; name: string }>>([])
const newPageType = ref<number | null>(null)
const router = useRouter()

const search = ref('')
const statusFilter = ref<string | null>(null)

const { items: pages, loading, loadingMore, hasMore, load, loadMore } = useInfiniteList<PageRow>(() => {
  const params = new URLSearchParams({ trash: '0' })
  if (search.value) params.set('search', search.value)
  if (statusFilter.value) params.set('status', statusFilter.value)
  return `/api/v1/pages/?${params}`
})
const sentinel = useInfiniteScrollSentinel(loadMore)

// Debounced so search doesn't fire a request per keystroke; filter changes (a
// single click) reload immediately since there's no typing to coalesce.
const debouncedLoad = useDebounceFn(load, 300)
watch(search, debouncedLoad)
watch(statusFilter, load)

async function loadPageTypes() {
  const resp = await useAuthFetch<{ results: any[] } | any[]>('/api/v1/page-types/')
  pageTypes.value = Array.isArray(resp) ? resp : resp.results
}

function titleFor(page: PageRow): string {
  const match = page.translations.find((tr) => tr.locale === locale.value)
  return match?.title || page.translations.find((tr) => tr.locale === 'en')?.title || page.slug
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

async function togglePublish(page: PageRow) {
  const action = page.status === 'published' ? 'unpublish' : 'publish'
  await useAuthFetch(`/api/v1/pages/${page.id}/${action}/`, { method: 'POST' })
  await load()
}

async function removePage(page: PageRow) {
  const ok = await confirm({
    message: t('pagesAdmin.deleteConfirm', { title: titleFor(page) }),
    danger: true,
  })
  if (!ok) return
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
      <h1 class="text-2xl font-black">{{ $t('pagesAdmin.title') }}</h1>
      <v-btn color="primary" @click="creating = true">
        <Icon name="solar:add-circle-bold-duotone" size="1.05rem" class="mr-1.5" />
        {{ $t('pagesAdmin.newPage') }}
      </v-btn>
    </div>

    <div v-if="creating" class="bento-card mt-6 flex flex-wrap items-end gap-3 p-4">
      <v-text-field v-model="newSlug" :label="$t('common.slug')" hide-details density="compact" style="max-width: 16rem" />
      <v-select
        v-model="newPageType"
        :items="pageTypes"
        item-title="name"
        item-value="id"
        :label="$t('pagesAdmin.pageType')"
        hide-details
        density="compact"
        style="max-width: 14rem"
      />
      <v-btn color="primary" @click="createPage">{{ $t('common.create') }}</v-btn>
      <v-btn variant="text" @click="creating = false">{{ $t('common.cancel') }}</v-btn>
    </div>

    <div class="mt-6 flex flex-wrap items-center gap-3">
      <v-text-field
        v-model="search"
        :placeholder="$t('pagesAdmin.searchPlaceholder')"
        hide-details
        density="compact"
        style="max-width: 18rem"
      >
        <template #prepend-inner><Icon name="solar:magnifer-bold-duotone" size="1.05rem" /></template>
      </v-text-field>
      <v-select
        v-model="statusFilter"
        :items="[
          { title: $t('status.allStatuses'), value: null },
          { title: $t('status.draft'), value: 'draft' },
          { title: $t('status.published'), value: 'published' },
          { title: $t('status.scheduled'), value: 'scheduled' },
          { title: $t('status.archived'), value: 'archived' },
        ]"
        hide-details
        density="compact"
        style="max-width: 12rem"
      />
    </div>

    <p v-if="loading" class="mt-4 text-sm" style="color: var(--text-faint)">{{ $t('common.loading') }}</p>
    <div v-else class="bento-card mt-4">
      <p v-if="!pages.length" class="px-4 py-6 text-sm" style="color: var(--text-faint)">
        {{ search || statusFilter ? $t('pagesAdmin.noPagesMatch') : $t('pagesAdmin.noPagesYet') }}
      </p>
      <div v-for="page in pages" :key="page.id" class="bento-row">
        <span class="bento-row__icon"><Icon name="solar:document-2-bold-duotone" /></span>
        <div class="bento-row__body">
          <div class="font-semibold">{{ titleFor(page) }}</div>
          <div class="text-xs" style="color: var(--text-faint)">/{{ page.slug }} — {{ $t(`status.${page.status}`) }}</div>
        </div>
        <div class="bento-row__actions">
          <button
            class="bento-icon-btn"
            :title="page.status === 'published' ? $t('common.unpublish') : $t('common.publish')"
            @click="togglePublish(page)"
          >
            <Icon :name="page.status === 'published' ? 'solar:eye-closed-bold-duotone' : 'solar:global-bold-duotone'" />
          </button>
          <a
            v-if="page.status === 'published'"
            :href="`/${page.full_path}`"
            target="_blank"
            rel="noopener"
            class="bento-icon-btn"
            :title="$t('pagesAdmin.openLivePage')"
          >
            <Icon name="solar:square-top-down-bold-duotone" />
          </a>
          <span v-else class="bento-icon-btn" style="opacity: 0.35; cursor: not-allowed" :title="$t('pagesAdmin.publishToViewLive')">
            <Icon name="solar:square-top-down-bold-duotone" />
          </span>
          <NuxtLink :to="`/admin/pages/${page.id}`" class="bento-icon-btn bento-icon-btn--primary" :title="$t('pagesAdmin.editBlocks')">
            <Icon name="solar:pen-2-bold-duotone" />
          </NuxtLink>
          <button class="bento-icon-btn bento-icon-btn--danger" :title="$t('common.delete')" @click="removePage(page)">
            <Icon name="solar:trash-bin-2-bold-duotone" />
          </button>
        </div>
      </div>
      <div v-if="pages.length" ref="sentinel" class="flex justify-center py-4">
        <span v-if="loadingMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.loadingMore') }}</span>
        <span v-else-if="!hasMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.endOfList') }}</span>
      </div>
    </div>
  </div>
</template>
