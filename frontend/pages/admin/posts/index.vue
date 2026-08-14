<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

const { confirm } = useConfirmDialog()
const { t, locale } = useI18n()

interface PostRow {
  id: number
  slug: string
  status: string
  published_at: string | null
  translations: Array<{ locale: string; title: string }>
}

const creating = ref(false)
const newSlug = ref('')
const router = useRouter()

const search = ref('')
const statusFilter = ref<string | null>(null)

const { items: posts, loading, loadingMore, hasMore, load, loadMore } = useInfiniteList<PostRow>(() => {
  const params = new URLSearchParams({ trash: '0' })
  if (search.value) params.set('search', search.value)
  if (statusFilter.value) params.set('status', statusFilter.value)
  return `/api/v1/posts/?${params}`
})
const sentinel = useInfiniteScrollSentinel(loadMore)

const debouncedLoad = useDebounceFn(load, 300)
watch(search, debouncedLoad)
watch(statusFilter, load)

function titleFor(post: PostRow): string {
  const match = post.translations.find((tr) => tr.locale === locale.value)
  return match?.title || post.translations.find((tr) => tr.locale === 'en')?.title || post.slug
}

async function createPost() {
  if (!newSlug.value) return
  const created = await useAuthFetch<PostRow>('/api/v1/posts/', {
    method: 'POST',
    body: { slug: newSlug.value, translations: [{ locale: 'en', title: newSlug.value }] },
  })
  creating.value = false
  newSlug.value = ''
  await router.push(`/admin/posts/${created.id}`)
}

async function togglePublish(post: PostRow) {
  const action = post.status === 'published' ? 'unpublish' : 'publish'
  await useAuthFetch(`/api/v1/posts/${post.id}/${action}/`, { method: 'POST' })
  await load()
}

async function removePost(post: PostRow) {
  const ok = await confirm({
    message: t('postsAdmin.deleteConfirm', { title: titleFor(post) }),
    danger: true,
  })
  if (!ok) return
  await useAuthFetch(`/api/v1/posts/${post.id}/`, { method: 'DELETE' })
  posts.value = posts.value.filter((p) => p.id !== post.id)
}

onMounted(load)

useSeoMeta({ title: 'Posts — CMS Admin' })
</script>

<template>
  <div>
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-black">{{ $t('postsAdmin.title') }}</h1>
      <div class="flex items-center gap-3">
        <NuxtLink to="/admin/categories" class="flex items-center gap-1 text-sm font-semibold" style="color: var(--text-secondary)">
          <Icon name="solar:folder-bold-duotone" size="1rem" /> {{ $t('postsAdmin.categories') }}
        </NuxtLink>
        <NuxtLink to="/admin/tags" class="flex items-center gap-1 text-sm font-semibold" style="color: var(--text-secondary)">
          <Icon name="solar:tag-bold-duotone" size="1rem" /> {{ $t('postsAdmin.tags') }}
        </NuxtLink>
        <v-btn color="primary" @click="creating = true">
          <Icon name="solar:add-circle-bold-duotone" size="1.05rem" class="mr-1.5" />
          {{ $t('postsAdmin.newPost') }}
        </v-btn>
      </div>
    </div>

    <div v-if="creating" class="bento-card mt-6 flex flex-wrap items-end gap-3 p-4">
      <v-text-field v-model="newSlug" :label="$t('common.slug')" hide-details density="compact" style="max-width: 16rem" />
      <v-btn color="primary" @click="createPost">{{ $t('common.create') }}</v-btn>
      <v-btn variant="text" @click="creating = false">{{ $t('common.cancel') }}</v-btn>
    </div>

    <div class="mt-6 flex flex-wrap items-center gap-3">
      <v-text-field
        v-model="search"
        :placeholder="$t('postsAdmin.searchPlaceholder')"
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
      <p v-if="!posts.length" class="px-4 py-6 text-sm" style="color: var(--text-faint)">
        {{ search || statusFilter ? $t('postsAdmin.noPostsMatch') : $t('postsAdmin.noPostsYet') }}
      </p>
      <div v-for="post in posts" :key="post.id" class="bento-row">
        <span class="bento-row__icon"><Icon name="solar:notes-bold-duotone" /></span>
        <div class="bento-row__body">
          <div class="font-semibold">{{ titleFor(post) }}</div>
          <div class="text-xs" style="color: var(--text-faint)">/post/{{ post.slug }} — {{ $t(`status.${post.status}`) }}</div>
        </div>
        <div class="bento-row__actions">
          <button
            class="bento-icon-btn"
            :title="post.status === 'published' ? $t('common.unpublish') : $t('common.publish')"
            @click="togglePublish(post)"
          >
            <Icon :name="post.status === 'published' ? 'solar:eye-closed-bold-duotone' : 'solar:global-bold-duotone'" />
          </button>
          <a
            v-if="post.status === 'published'"
            :href="`/post/${post.slug}`"
            target="_blank"
            rel="noopener"
            class="bento-icon-btn"
            :title="$t('postsAdmin.openLivePost')"
          >
            <Icon name="solar:square-top-down-bold-duotone" />
          </a>
          <span v-else class="bento-icon-btn" style="opacity: 0.35; cursor: not-allowed" :title="$t('pagesAdmin.publishToViewLive')">
            <Icon name="solar:square-top-down-bold-duotone" />
          </span>
          <NuxtLink :to="`/admin/posts/${post.id}`" class="bento-icon-btn bento-icon-btn--primary" :title="$t('pagesAdmin.editBlocks')">
            <Icon name="solar:pen-2-bold-duotone" />
          </NuxtLink>
          <button class="bento-icon-btn bento-icon-btn--danger" :title="$t('common.delete')" @click="removePost(post)">
            <Icon name="solar:trash-bin-2-bold-duotone" />
          </button>
        </div>
      </div>
      <div v-if="posts.length" ref="sentinel" class="flex justify-center py-4">
        <span v-if="loadingMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.loadingMore') }}</span>
        <span v-else-if="!hasMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.endOfList') }}</span>
      </div>
    </div>
  </div>
</template>
