<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

interface Choice {
  id?: number
  text: Record<string, string>
  is_correct: boolean
}
interface Question {
  id?: number
  text: Record<string, string>
  choices: Choice[]
}

const route = useRoute()
const quizId = route.params.id as string
const { t, locale } = useI18n()

// Which locale variant of title/description/questions/choices the editor
// shows/edits — same rationale as the block builder's propLocale.
const propLocale = ref<'en' | 'km'>('en')

const quiz = ref<any>(null)
const titleByLocale = reactive<Record<string, string>>({ en: '', km: '' })
const slug = ref('')
const descriptionByLocale = reactive<Record<string, string>>({ en: '', km: '' })
const questions = ref<Question[]>([])
const saveStatus = ref('')
const saving = ref(false)

const tab = ref<'edit' | 'results'>('edit')
const analytics = ref<any>(null)
const loadingAnalytics = ref(false)

const questionItemFields = computed(() => [
  { key: 'text', type: 'text', translatable: true, label: t('quizzesAdmin.questionText') },
  {
    key: 'choices',
    type: 'list',
    label: t('quizzesAdmin.choices'),
    itemFields: [
      { key: 'text', type: 'text', translatable: true, label: t('quizzesAdmin.choiceText') },
      { key: 'is_correct', type: 'boolean', label: t('quizzesAdmin.correctAnswer') },
    ],
  },
])

function titleFor(row: { title?: Record<string, string> }): string {
  return row.title?.[locale.value] || row.title?.en || ''
}

async function loadQuiz() {
  quiz.value = await useAuthFetch<any>(`/api/v1/quizzes/${quizId}/`)
  titleByLocale.en = quiz.value.title?.en || ''
  titleByLocale.km = quiz.value.title?.km || ''
  slug.value = quiz.value.slug
  descriptionByLocale.en = quiz.value.description?.en || ''
  descriptionByLocale.km = quiz.value.description?.km || ''
  questions.value = quiz.value.questions || []
}

async function loadAnalytics() {
  loadingAnalytics.value = true
  analytics.value = await useAuthFetch<any>(`/api/v1/quizzes/${quizId}/analytics/`)
  loadingAnalytics.value = false
}

watch(tab, (t) => {
  if (t === 'results' && !analytics.value) loadAnalytics()
})

onMounted(loadQuiz)

async function togglePublish() {
  if (!quiz.value) return
  await useAuthFetch(`/api/v1/quizzes/${quizId}/`, { method: 'PATCH', body: { is_published: !quiz.value.is_published } })
  await loadQuiz()
}

async function save() {
  saving.value = true
  saveStatus.value = ''
  try {
    // Strip client-only bookkeeping (`id` on brand-new question/choice rows
    // added via "Add item" would be undefined anyway) — the backend replaces
    // the whole question/choice tree on every save, so only text/is_correct
    // matter here.
    const payload = {
      title: { en: titleByLocale.en, km: titleByLocale.km },
      slug: slug.value,
      description: { en: descriptionByLocale.en, km: descriptionByLocale.km },
      questions: questions.value.map((q) => ({
        text: q.text,
        choices: (q.choices || []).map((c) => ({ text: c.text, is_correct: !!c.is_correct })),
      })),
    }
    await useAuthFetch(`/api/v1/quizzes/${quizId}/`, { method: 'PATCH', body: payload })
    await loadQuiz()
    saveStatus.value = 'saved'
    setTimeout(() => (saveStatus.value = ''), 1500)
  } finally {
    saving.value = false
  }
}

useSeoMeta({ title: 'Quiz Builder — CMS Admin' })
</script>

<template>
  <div class="mx-auto max-w-3xl px-6 py-6">
    <div class="flex items-center justify-between">
      <NuxtLink to="/admin/quizzes" class="flex items-center gap-1 text-sm" style="color: var(--text-faint)">
        <Icon name="solar:alt-arrow-left-linear" size="0.95rem" /> {{ $t('quizzesAdmin.title') }}
      </NuxtLink>
      <div class="flex items-center gap-2">
        <div class="bento-pill-group">
          <button class="bento-pill" :class="{ 'bento-pill--active': propLocale === 'en' }" @click="propLocale = 'en'">EN</button>
          <button class="bento-pill" :class="{ 'bento-pill--active': propLocale === 'km' }" @click="propLocale = 'km'">ខ្មែរ</button>
        </div>
        <span
          class="rounded-full px-2 py-0.5 text-xs font-semibold"
          :style="
            quiz?.is_published
              ? 'background: var(--success-bg); color: var(--success)'
              : 'background: var(--surface-2); color: var(--text-faint)'
          "
        >
          {{ quiz?.is_published ? $t('status.published') : $t('status.draft') }}
        </span>
        <button class="bento-icon-btn" :title="quiz?.is_published ? $t('blockBuilder.unpublish') : $t('blockBuilder.publish')" @click="togglePublish">
          <Icon :name="quiz?.is_published ? 'solar:eye-closed-bold-duotone' : 'solar:global-bold-duotone'" size="1rem" />
        </button>
      </div>
    </div>

    <h1 class="mt-4 text-2xl font-black">{{ titleByLocale[propLocale] || $t('quizzesAdmin.title') }}</h1>

    <div class="bento-pill-group mt-4">
      <button class="bento-pill" :class="{ 'bento-pill--active': tab === 'edit' }" @click="tab = 'edit'">{{ $t('quizzesAdmin.editTab') }}</button>
      <button class="bento-pill" :class="{ 'bento-pill--active': tab === 'results' }" @click="tab = 'results'">{{ $t('quizzesAdmin.resultsTab') }}</button>
    </div>

    <div v-if="tab === 'edit'" class="mt-4 space-y-4">
      <div class="bento-card p-4">
        <v-text-field v-model="titleByLocale[propLocale]" :label="$t('quizzesAdmin.titleLabel')" hide-details density="compact" />
        <v-text-field v-model="slug" :label="$t('common.slug')" class="mt-3" hide-details density="compact" />
        <v-textarea v-model="descriptionByLocale[propLocale]" :label="$t('quizzesAdmin.description')" rows="2" class="mt-3" hide-details density="compact" />
      </div>

      <div class="bento-card p-4">
        <h2 class="text-xs font-bold uppercase" style="color: var(--text-faint)">{{ $t('quizzesAdmin.questions') }}</h2>
        <ListFieldEditor v-model="questions" class="mt-3" :item-fields="questionItemFields" :locale="propLocale" />
      </div>

      <div class="flex items-center gap-3">
        <v-btn color="primary" :loading="saving" @click="save">
          <Icon name="solar:diskette-bold-duotone" size="1.05rem" class="mr-1.5" />
          {{ $t('quizzesAdmin.saveQuiz') }}
        </v-btn>
        <span v-if="saveStatus" class="flex items-center gap-1 text-xs" style="color: var(--success)">
          <Icon name="solar:check-circle-bold-duotone" size="0.95rem" />
          {{ $t('blockBuilder.saved') }}
        </span>
      </div>
    </div>

    <div v-else class="mt-4">
      <p v-if="loadingAnalytics" class="text-sm" style="color: var(--text-faint)">{{ $t('common.loading') }}</p>
      <template v-else-if="analytics">
        <div class="grid grid-cols-2 gap-4">
          <div class="bento-tile">
            <span class="bento-tile__icon bento-tile__icon--ember"><Icon name="solar:users-group-rounded-bold-duotone" /></span>
            <div class="text-2xl font-black">{{ analytics.attempt_count }}</div>
            <div class="text-xs" style="color: var(--text-faint)">{{ $t('quizzesAdmin.attempts') }}</div>
          </div>
          <div class="bento-tile">
            <span class="bento-tile__icon bento-tile__icon--success"><Icon name="solar:medal-star-bold-duotone" /></span>
            <div class="text-2xl font-black">{{ analytics.average_score }}</div>
            <div class="text-xs" style="color: var(--text-faint)">{{ $t('quizzesAdmin.averageScore') }}</div>
          </div>
        </div>

        <div v-if="!analytics.attempt_count" class="bento-card mt-4 p-4 text-sm" style="color: var(--text-faint)">
          {{ $t('quizzesAdmin.noAttemptsYet') }}
        </div>
        <div v-for="q in analytics.questions" :key="q.id" class="bento-card mt-4 p-4">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-bold">{{ titleFor({ title: q.text }) }}</h3>
            <span class="text-xs" style="color: var(--text-faint)">{{ $t('quizzesAdmin.percentCorrect', { pct: q.correct_rate }) }}</span>
          </div>
          <div v-for="c in q.choices" :key="c.id" class="mt-2">
            <div class="flex items-center justify-between text-xs">
              <span :style="c.is_correct ? 'color: var(--success); font-weight: 600' : ''">
                {{ titleFor({ title: c.text }) }}
                <Icon v-if="c.is_correct" name="solar:check-circle-bold-duotone" size="0.85rem" class="ml-0.5" />
              </span>
              <span style="color: var(--text-faint)">{{ c.count }} ({{ c.percentage }}%)</span>
            </div>
            <div class="mt-1 h-1.5 overflow-hidden rounded-full" style="background: var(--surface-2)">
              <div
                class="h-full rounded-full"
                :style="{ width: `${c.percentage}%`, background: c.is_correct ? 'var(--success)' : 'var(--ember)' }"
              />
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
