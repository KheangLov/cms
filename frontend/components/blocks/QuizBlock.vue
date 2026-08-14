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

// Same {en,km}-dict lookup as t() above, but for values fetched straight
// from the Quiz API (title/description/question/choice text) rather than
// block props — same shape, different source.
function tr(value: any): string {
  if (value && typeof value === 'object') {
    return value[props.locale || 'en'] ?? value.en ?? ''
  }
  return value ?? ''
}

const { t: $t } = useI18n()

const config = useRuntimeConfig()
const apiBase = (import.meta.server ? config.apiBaseInternal : config.public.apiBase) as string

const quizId = computed<number | null>(() => props.block.props.quizId ?? null)

const { data: quiz } = await useFetch<any>(`/api/v1/quizzes/${quizId.value}/`, {
  key: `quiz-embed-${props.block.id}`,
  baseURL: apiBase,
  immediate: !!quizId.value,
})

const answers = reactive<Record<number, number>>({})
const submitting = ref(false)
const errorMessage = ref('')
const result = ref<any>(null)

const allAnswered = computed(() => {
  if (!quiz.value) return false
  return quiz.value.questions.every((q: any) => answers[q.id] != null)
})

function correctnessFor(questionId: number) {
  return result.value?.per_question?.find((pq: any) => pq.question_id === questionId)
}
function choiceText(question: any, choiceId: number | undefined) {
  return tr(question.choices.find((c: any) => c.id === choiceId)?.text) || ''
}

async function submit() {
  submitting.value = true
  errorMessage.value = ''
  try {
    result.value = await $fetch(`/api/v1/quizzes/${quizId.value}/attempt/`, {
      method: 'POST',
      baseURL: apiBase,
      body: { answers: Object.entries(answers).map(([questionId, choiceId]) => ({ question_id: Number(questionId), choice_id: choiceId })) },
    })
  } catch {
    errorMessage.value = $t('publicQuiz.error')
  } finally {
    submitting.value = false
  }
}

function retake() {
  for (const key of Object.keys(answers)) delete answers[Number(key)]
  result.value = null
}
</script>

<template>
  <section class="mx-auto max-w-2xl px-6 py-10">
    <h2 v-if="t('heading')" class="mb-2 text-2xl font-black">{{ t('heading') }}</h2>

    <template v-if="quiz">
      <h3 class="text-xl font-bold">{{ tr(quiz.title) }}</h3>
      <p v-if="tr(quiz.description)" class="mt-1 text-sm" style="color: var(--text-secondary)">{{ tr(quiz.description) }}</p>

      <div v-if="result" class="mt-6 space-y-4">
        <div class="bento-card p-5 text-center">
          <div class="text-3xl font-black">{{ result.score }} / {{ result.total_questions }}</div>
          <p class="mt-1 text-sm" style="color: var(--text-faint)">{{ $t('publicQuiz.yourScore') }}</p>
        </div>
        <div v-for="(question, qi) in quiz.questions" :key="question.id" class="bento-card p-4">
          <p class="font-semibold">{{ qi + 1 }}. {{ tr(question.text) }}</p>
          <div
            class="mt-2 flex items-center gap-1.5 text-sm"
            :style="correctnessFor(question.id)?.correct ? 'color: var(--success)' : 'color: var(--error)'"
          >
            <Icon :name="correctnessFor(question.id)?.correct ? 'solar:check-circle-bold-duotone' : 'solar:close-circle-bold-duotone'" size="1rem" />
            {{ choiceText(question, answers[question.id]) }}
          </div>
          <p v-if="!correctnessFor(question.id)?.correct" class="mt-1 text-xs" style="color: var(--text-faint)">
            {{ $t('publicQuiz.correctAnswer') }} {{ choiceText(question, correctnessFor(question.id)?.correct_choice_id) }}
          </p>
        </div>
        <v-btn variant="tonal" block @click="retake">{{ $t('publicQuiz.retake') }}</v-btn>
      </div>

      <form v-else class="mt-6 space-y-4" @submit.prevent="submit">
        <div v-for="(question, qi) in quiz.questions" :key="question.id" class="bento-card p-4">
          <p class="font-semibold">{{ qi + 1 }}. {{ tr(question.text) }}</p>
          <div class="mt-3 space-y-1">
            <label
              v-for="choice in question.choices"
              :key="choice.id"
              class="flex cursor-pointer items-center gap-2 rounded-lg p-2 text-sm"
              style="transition: background 0.15s ease"
            >
              <input v-model="answers[question.id]" type="radio" :name="`question-${question.id}`" :value="choice.id" />
              {{ tr(choice.text) }}
            </label>
          </div>
        </div>
        <p v-if="errorMessage" class="text-xs" style="color: var(--error)">{{ errorMessage }}</p>
        <v-btn color="primary" block type="submit" :disabled="!allAnswered" :loading="submitting">{{ $t('publicQuiz.submit') }}</v-btn>
      </form>
    </template>
    <p v-else class="text-sm" style="color: var(--text-faint)">
      {{ quizId ? $t('publicQuiz.loading') : $t('publicQuiz.noneSelected') }}
    </p>
  </section>
</template>
