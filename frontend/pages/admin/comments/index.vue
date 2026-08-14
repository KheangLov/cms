<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

const { confirm } = useConfirmDialog()
const { t } = useI18n()

interface CommentRow {
  id: number
  resolved_target_type: string
  object_id: number
  author_email: string | null
  body: string
  status: string
  created_at: string
}

const filter = ref<'pending' | 'approved' | 'spam' | 'all'>('pending')
const search = ref('')

const { items: comments, loading, loadingMore, hasMore, load, loadMore } = useInfiniteList<CommentRow>(() => {
  const params = new URLSearchParams()
  if (filter.value !== 'all') params.set('status', filter.value)
  if (search.value) params.set('search', search.value)
  return `/api/v1/comments/?${params}`
})
const sentinel = useInfiniteScrollSentinel(loadMore)

watch(search, useDebounceFn(load, 300))

async function approve(comment: CommentRow) {
  await useAuthFetch(`/api/v1/comments/${comment.id}/approve/`, { method: 'POST' })
  await load()
}

async function reject(comment: CommentRow) {
  await useAuthFetch(`/api/v1/comments/${comment.id}/reject/`, { method: 'POST' })
  await load()
}

async function remove(comment: CommentRow) {
  if (!(await confirm({ message: t('commentsAdmin.deleteConfirm'), danger: true }))) return
  await useAuthFetch(`/api/v1/comments/${comment.id}/`, { method: 'DELETE' })
  await load()
}

watch(filter, load)
onMounted(load)

useSeoMeta({ title: 'Comments — CMS Admin' })
</script>

<template>
  <div>
    <h1 class="text-2xl font-black">{{ $t('nav.comments') }}</h1>

    <div class="mt-6 flex flex-wrap items-center gap-3">
      <v-text-field
        v-model="search"
        :placeholder="$t('commentsAdmin.searchPlaceholder')"
        hide-details
        density="compact"
        style="max-width: 18rem"
      >
        <template #prepend-inner><Icon name="solar:magnifer-bold-duotone" size="1.05rem" /></template>
      </v-text-field>
      <Icon name="solar:filter-bold-duotone" size="1rem" style="color: var(--text-faint)" />
      <div class="bento-pill-group">
        <button
          v-for="opt in ['pending', 'approved', 'spam', 'all']"
          :key="opt"
          class="bento-pill"
          :class="{ 'bento-pill--active': filter === opt }"
          @click="filter = opt as any"
        >
          {{ $t(`commentsAdmin.filter${opt.charAt(0).toUpperCase() + opt.slice(1)}`) }}
        </button>
      </div>
    </div>

    <p v-if="loading" class="mt-4 text-sm" style="color: var(--text-faint)">{{ $t('common.loading') }}</p>
    <p v-else-if="!comments.length" class="mt-4 text-sm" style="color: var(--text-faint)">
      {{ search ? $t('commentsAdmin.noCommentsMatch') : $t('commentsAdmin.nothingHere') }}
    </p>
    <div v-else class="bento-card mt-4">
      <div v-for="comment in comments" :key="comment.id" class="bento-row" style="align-items: flex-start">
        <span class="bento-row__icon"><Icon name="solar:chat-round-dots-bold-duotone" /></span>
        <div class="bento-row__body">
          <div class="flex items-center justify-between text-xs" style="color: var(--text-faint)">
            <span>
              <strong style="color: var(--text-secondary)">{{ comment.author_email || $t('commentsAdmin.unknown') }}</strong>
              {{ $t('commentsAdmin.onTarget', { type: comment.resolved_target_type, id: comment.object_id }) }}
            </span>
            <span>{{ new Date(comment.created_at).toLocaleString() }}</span>
          </div>
          <p class="mt-1 text-sm">{{ comment.body }}</p>
        </div>
        <div class="bento-row__actions">
          <button
            v-if="comment.status !== 'approved'"
            class="bento-icon-btn bento-icon-btn--success"
            :title="$t('common.approve')"
            @click="approve(comment)"
          >
            <Icon name="solar:check-circle-bold-duotone" />
          </button>
          <button v-if="comment.status !== 'spam'" class="bento-icon-btn" :title="$t('commentsAdmin.markSpam')" @click="reject(comment)">
            <Icon name="solar:flag-2-bold-duotone" />
          </button>
          <button class="bento-icon-btn bento-icon-btn--danger" :title="$t('common.delete')" @click="remove(comment)">
            <Icon name="solar:trash-bin-2-bold-duotone" />
          </button>
        </div>
      </div>
      <div v-if="comments.length" ref="sentinel" class="flex justify-center py-4">
        <span v-if="loadingMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.loadingMore') }}</span>
        <span v-else-if="!hasMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.endOfList') }}</span>
      </div>
    </div>
  </div>
</template>
