<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

const { confirm } = useConfirmDialog()
const { t, locale } = useI18n()

interface QuizRow {
  id: number
  title: Record<string, string>
  slug: string
  is_published: boolean
  questions: unknown[]
}

function titleFor(row: { title: Record<string, string> }): string {
  return row.title?.[locale.value] || row.title?.en || ''
}

const creating = ref(false)
const newTitle = ref('')
const router = useRouter()

const search = ref('')

const { items: quizzes, loading, loadingMore, hasMore, load, loadMore } = useInfiniteList<QuizRow>(() => {
  const params = new URLSearchParams()
  if (search.value) params.set('search', search.value)
  return `/api/v1/quizzes/?${params}`
})
const sentinel = useInfiniteScrollSentinel(loadMore)

watch(search, useDebounceFn(load, 300))
onMounted(load)

function slugify(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '')
}

async function createQuiz() {
  if (!newTitle.value.trim()) return
  const created = await useAuthFetch<QuizRow>('/api/v1/quizzes/', {
    method: 'POST',
    body: { title: { en: newTitle.value }, slug: slugify(newTitle.value) },
  })
  creating.value = false
  newTitle.value = ''
  await router.push(`/admin/quizzes/${created.id}`)
}

async function togglePublish(quiz: QuizRow) {
  await useAuthFetch(`/api/v1/quizzes/${quiz.id}/`, { method: 'PATCH', body: { is_published: !quiz.is_published } })
  await load()
}

async function removeQuiz(quiz: QuizRow) {
  const ok = await confirm({ message: t('quizzesAdmin.deleteConfirm', { title: titleFor(quiz) }), danger: true })
  if (!ok) return
  await useAuthFetch(`/api/v1/quizzes/${quiz.id}/`, { method: 'DELETE' })
  quizzes.value = quizzes.value.filter((q) => q.id !== quiz.id)
}

useSeoMeta({ title: 'Quizzes — CMS Admin' })
</script>

<template>
  <div>
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-black">{{ $t('quizzesAdmin.title') }}</h1>
      <v-btn color="primary" @click="creating = true">
        <Icon name="solar:add-circle-bold-duotone" size="1.05rem" class="mr-1.5" />
        {{ $t('quizzesAdmin.newQuiz') }}
      </v-btn>
    </div>

    <div v-if="creating" class="bento-card mt-6 flex flex-wrap items-end gap-3 p-4">
      <v-text-field v-model="newTitle" :label="$t('quizzesAdmin.titleLabel')" hide-details density="compact" style="max-width: 20rem" @keyup.enter="createQuiz" />
      <v-btn color="primary" @click="createQuiz">{{ $t('common.create') }}</v-btn>
      <v-btn variant="text" @click="creating = false">{{ $t('common.cancel') }}</v-btn>
    </div>

    <div class="mt-6 flex flex-wrap items-center gap-3">
      <v-text-field
        v-model="search"
        :placeholder="$t('quizzesAdmin.searchPlaceholder')"
        hide-details
        density="compact"
        style="max-width: 18rem"
      >
        <template #prepend-inner><Icon name="solar:magnifer-bold-duotone" size="1.05rem" /></template>
      </v-text-field>
    </div>

    <p v-if="loading" class="mt-4 text-sm" style="color: var(--text-faint)">{{ $t('common.loading') }}</p>
    <div v-else class="bento-card mt-4">
      <p v-if="!quizzes.length" class="px-4 py-6 text-sm" style="color: var(--text-faint)">
        {{ search ? $t('quizzesAdmin.noQuizzesMatch') : $t('quizzesAdmin.noQuizzesYet') }}
      </p>
      <div v-for="quiz in quizzes" :key="quiz.id" class="bento-row">
        <span class="bento-row__icon"><Icon name="solar:clipboard-check-bold-duotone" /></span>
        <div class="bento-row__body">
          <div class="font-semibold">{{ titleFor(quiz) }}</div>
          <div class="text-xs" style="color: var(--text-faint)">
            /{{ quiz.slug }} — {{ quiz.is_published ? $t('status.published') : $t('status.draft') }} — {{ $t('quizzesAdmin.questionCount', { n: quiz.questions?.length ?? 0 }) }}
          </div>
        </div>
        <div class="bento-row__actions">
          <button
            class="bento-icon-btn"
            :title="quiz.is_published ? $t('blockBuilder.unpublish') : $t('blockBuilder.publish')"
            @click="togglePublish(quiz)"
          >
            <Icon :name="quiz.is_published ? 'solar:eye-closed-bold-duotone' : 'solar:global-bold-duotone'" />
          </button>
          <NuxtLink :to="`/admin/quizzes/${quiz.id}`" class="bento-icon-btn bento-icon-btn--primary" :title="$t('common.edit')">
            <Icon name="solar:pen-2-bold-duotone" />
          </NuxtLink>
          <button class="bento-icon-btn bento-icon-btn--danger" :title="$t('common.delete')" @click="removeQuiz(quiz)">
            <Icon name="solar:trash-bin-2-bold-duotone" />
          </button>
        </div>
      </div>
      <div v-if="quizzes.length" ref="sentinel" class="flex justify-center py-4">
        <span v-if="loadingMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.loadingMore') }}</span>
        <span v-else-if="!hasMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.endOfList') }}</span>
      </div>
    </div>
  </div>
</template>
