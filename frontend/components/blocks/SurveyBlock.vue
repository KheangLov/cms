<script setup lang="ts">
interface Props {
  block: { id: number; props: Record<string, any> }
  locale?: string
}
const props = defineProps<Props>()

function t(field: string): string {
  const value = props.block.props[field]
  if (value && typeof value === 'object') {
    return value[props.locale || 'en'] ?? value.en ?? ''
  }
  return value ?? ''
}

function tr(value: any): string {
  if (value && typeof value === 'object') {
    return value[props.locale || 'en'] ?? value.en ?? ''
  }
  return value ?? ''
}

const { t: $t } = useI18n()

const config = useRuntimeConfig()
const apiBase = (import.meta.server ? config.apiBaseInternal : config.public.apiBase) as string

const surveyId = computed<number | null>(() => props.block.props.surveyId ?? null)

const { data: survey } = await useFetch<any>(`/api/v1/surveys/${surveyId.value}/`, {
  key: `survey-embed-${props.block.id}`,
  baseURL: apiBase,
  immediate: !!surveyId.value,
})

const choiceAnswers = reactive<Record<number, number>>({})
const textAnswers = reactive<Record<number, string>>({})
const submitting = ref(false)
const submitted = ref(false)
const errorMessage = ref('')

const allAnswered = computed(() => {
  if (!survey.value) return false
  return survey.value.questions.every((q: any) =>
    q.question_type === 'choice' ? choiceAnswers[q.id] != null : (textAnswers[q.id] || '').trim() !== '',
  )
})

async function submit() {
  submitting.value = true
  errorMessage.value = ''
  try {
    const answers = survey.value.questions.map((q: any) =>
      q.question_type === 'choice'
        ? { question_id: q.id, choice_id: choiceAnswers[q.id] }
        : { question_id: q.id, text: textAnswers[q.id] },
    )
    await $fetch(`/api/v1/surveys/${surveyId.value}/respond/`, {
      method: 'POST',
      baseURL: apiBase,
      body: { answers },
    })
    submitted.value = true
  } catch {
    errorMessage.value = $t('publicQuiz.error')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="mx-auto max-w-2xl px-6 py-10">
    <h2 v-if="t('heading')" class="mb-2 text-2xl font-black">{{ t('heading') }}</h2>

    <template v-if="survey">
      <div v-if="submitted" class="bento-card mt-4 p-6 text-center">
        <Icon name="solar:check-circle-bold-duotone" size="2rem" style="color: var(--success)" />
        <p class="mt-2 font-semibold">{{ $t('publicSurvey.thankYou') }}</p>
      </div>

      <template v-else>
        <h3 class="text-xl font-bold">{{ tr(survey.title) }}</h3>
        <p v-if="tr(survey.description)" class="mt-1 text-sm" style="color: var(--text-secondary)">{{ tr(survey.description) }}</p>

        <form class="mt-6 space-y-4" @submit.prevent="submit">
          <div v-for="(question, qi) in survey.questions" :key="question.id" class="bento-card p-4">
            <p class="font-semibold">{{ qi + 1 }}. {{ tr(question.text) }}</p>
            <div v-if="question.question_type === 'choice'" class="mt-3 space-y-1">
              <label
                v-for="choice in question.choices"
                :key="choice.id"
                class="flex cursor-pointer items-center gap-2 rounded-lg p-2 text-sm"
              >
                <input v-model="choiceAnswers[question.id]" type="radio" :name="`survey-question-${question.id}`" :value="choice.id" />
                {{ tr(choice.text) }}
              </label>
            </div>
            <textarea
              v-else
              v-model="textAnswers[question.id]"
              class="bento-input mt-3"
              rows="3"
              :placeholder="$t('publicSurvey.yourAnswer')"
            />
          </div>
          <p v-if="errorMessage" class="text-xs" style="color: var(--error)">{{ errorMessage }}</p>
          <v-btn color="primary" block type="submit" :disabled="!allAnswered" :loading="submitting">{{ $t('publicQuiz.submit') }}</v-btn>
        </form>
      </template>
    </template>
    <p v-else class="text-sm" style="color: var(--text-faint)">
      {{ surveyId ? $t('publicSurvey.loading') : $t('publicSurvey.noneSelected') }}
    </p>
  </section>
</template>
