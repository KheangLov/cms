// Backs the "reference" block-prop field type — a dropdown that picks another
// entity (e.g. a Quiz) by id instead of an editor typing a raw number. Module-
// scope singleton cache (same pattern as useConfirmDialog) since the option
// list is shared, not per-builder-instance state.
const referenceOptions = reactive<Record<string, any[]>>({})

const REFERENCE_ENDPOINTS: Record<string, string> = {
  quiz: '/api/v1/quizzes/',
  survey: '/api/v1/surveys/',
}

export function useReferenceOptions() {
  async function ensureReferenceOptions(referenceType?: string) {
    if (!referenceType || referenceOptions[referenceType] || !REFERENCE_ENDPOINTS[referenceType]) return
    const resp = await useAuthFetch<{ results: any[] } | any[]>(REFERENCE_ENDPOINTS[referenceType])
    referenceOptions[referenceType] = Array.isArray(resp) ? resp : resp.results
  }

  function optionsFor(referenceType?: string): any[] {
    return referenceType ? referenceOptions[referenceType] || [] : []
  }

  return { ensureReferenceOptions, optionsFor }
}
