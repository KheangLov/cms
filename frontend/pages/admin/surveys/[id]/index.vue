<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

interface Choice {
  id?: number
  text: Record<string, string>
}
interface Question {
  id?: number
  text: Record<string, string>
  question_type: 'choice' | 'text'
  choices: Choice[]
}

const route = useRoute()
const surveyId = route.params.id as string
const { t, locale } = useI18n()

const propLocale = ref<'en' | 'km'>('en')

const survey = ref<any>(null)
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
    key: 'question_type',
    type: 'select',
    label: t('surveysAdmin.questionType'),
    options: [
      { title: t('surveysAdmin.choiceOption'), value: 'choice' },
      { title: t('surveysAdmin.textOption'), value: 'text' },
    ],
  },
  {
    key: 'choices',
    type: 'list',
    label: t('surveysAdmin.choicesHint'),
    itemFields: [{ key: 'text', type: 'text', translatable: true, label: t('quizzesAdmin.choiceText') }],
  },
])

function titleFor(row: { title?: Record<string, string> }): string {
  return row.title?.[locale.value] || row.title?.en || ''
}

async function loadSurvey() {
  survey.value = await useAuthFetch<any>(`/api/v1/surveys/${surveyId}/`)
  titleByLocale.en = survey.value.title?.en || ''
  titleByLocale.km = survey.value.title?.km || ''
  slug.value = survey.value.slug
  descriptionByLocale.en = survey.value.description?.en || ''
  descriptionByLocale.km = survey.value.description?.km || ''
  questions.value = survey.value.questions || []
}

async function loadAnalytics() {
  loadingAnalytics.value = true
  analytics.value = await useAuthFetch<any>(`/api/v1/surveys/${surveyId}/analytics/`)
  loadingAnalytics.value = false
}

watch(tab, (t) => {
  if (t === 'results' && !analytics.value) loadAnalytics()
})

onMounted(loadSurvey)

async function togglePublish() {
  if (!survey.value) return
  await useAuthFetch(`/api/v1/surveys/${surveyId}/`, { method: 'PATCH', body: { is_published: !survey.value.is_published } })
  await loadSurvey()
}

async function save() {
  saving.value = true
  saveStatus.value = ''
  try {
    const payload = {
      title: { en: titleByLocale.en, km: titleByLocale.km },
      slug: slug.value,
      description: { en: descriptionByLocale.en, km: descriptionByLocale.km },
      questions: questions.value.map((q) => ({
        text: q.text,
        question_type: q.question_type || 'choice',
        choices: q.question_type === 'text' ? [] : (q.choices || []).map((c) => ({ text: c.text })),
      })),
    }
    await useAuthFetch(`/api/v1/surveys/${surveyId}/`, { method: 'PATCH', body: payload })
    await loadSurvey()
    saveStatus.value = 'saved'
    setTimeout(() => (saveStatus.value = ''), 1500)
  } finally {
    saving.value = false
  }
}

useSeoMeta({ title: 'Survey Builder — CMS Admin' })
</script>

<template>
  <div class="mx-auto max-w-3xl px-6 py-6">
    <div class="flex items-center justify-between">
      <NuxtLink to="/admin/surveys" class="flex items-center gap-1 text-sm" style="color: var(--text-faint)">
        <Icon name="solar:alt-arrow-left-linear" size="0.95rem" /> {{ $t('surveysAdmin.title') }}
      </NuxtLink>
      <div class="flex items-center gap-2">
        <div class="bento-pill-group">
          <button class="bento-pill" :class="{ 'bento-pill--active': propLocale === 'en' }" @click="propLocale = 'en'">EN</button>
          <button class="bento-pill" :class="{ 'bento-pill--active': propLocale === 'km' }" @click="propLocale = 'km'">ខ្មែរ</button>
        </div>
        <span
          class="rounded-full px-2 py-0.5 text-xs font-semibold"
          :style="
            survey?.is_published
              ? 'background: var(--success-bg); color: var(--success)'
              : 'background: var(--surface-2); color: var(--text-faint)'
          "
        >
          {{ survey?.is_published ? $t('status.published') : $t('status.draft') }}
        </span>
        <button class="bento-icon-btn" :title="survey?.is_published ? $t('blockBuilder.unpublish') : $t('blockBuilder.publish')" @click="togglePublish">
          <Icon :name="survey?.is_published ? 'solar:eye-closed-bold-duotone' : 'solar:global-bold-duotone'" size="1rem" />
        </button>
      </div>
    </div>

    <h1 class="mt-4 text-2xl font-black">{{ titleByLocale[propLocale] || $t('surveysAdmin.title') }}</h1>

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
          {{ $t('surveysAdmin.saveSurvey') }}
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
        <div class="bento-tile" style="max-width: 12rem">
          <span class="bento-tile__icon bento-tile__icon--ember"><Icon name="solar:users-group-rounded-bold-duotone" /></span>
          <div class="text-2xl font-black">{{ analytics.response_count }}</div>
          <div class="text-xs" style="color: var(--text-faint)">{{ $t('surveysAdmin.responses') }}</div>
        </div>

        <div v-if="!analytics.response_count" class="bento-card mt-4 p-4 text-sm" style="color: var(--text-faint)">
          {{ $t('surveysAdmin.noResponsesYet') }}
        </div>

        <div v-for="q in analytics.questions" :key="q.id" class="bento-card mt-4 p-4">
          <h3 class="text-sm font-bold">{{ titleFor({ title: q.text }) }}</h3>

          <template v-if="q.question_type === 'choice'">
            <div v-for="c in q.choices" :key="c.id" class="mt-2">
              <div class="flex items-center justify-between text-xs">
                <span>{{ titleFor({ title: c.text }) }}</span>
                <span style="color: var(--text-faint)">{{ c.count }} ({{ c.percentage }}%)</span>
              </div>
              <div class="mt-1 h-1.5 overflow-hidden rounded-full" style="background: var(--surface-2)">
                <div class="h-full rounded-full" :style="{ width: `${c.percentage}%`, background: 'var(--ember)' }" />
              </div>
            </div>
          </template>
          <template v-else>
            <p class="mt-1 text-xs" style="color: var(--text-faint)">{{ $t('surveysAdmin.responseCount', { n: q.answer_count }) }}</p>
            <ul v-if="q.recent_answers?.length" class="mt-2 space-y-2">
              <li v-for="(answer, i) in q.recent_answers" :key="i" class="rounded-lg p-2 text-sm" style="background: var(--surface-2)">
                {{ answer }}
              </li>
            </ul>
          </template>
        </div>
      </template>
    </div>
  </div>
</template>
