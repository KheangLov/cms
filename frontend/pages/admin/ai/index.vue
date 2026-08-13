<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

const providers = ref<Record<string, boolean>>({})
const providerChoice = ref('openai')

const prompt = ref('')
const genResult = ref('')
const genError = ref('')
const genBusy = ref(false)

const translateText = ref('')
const sourceLocale = ref('en')
const targetLocale = ref('km')
const translateResult = ref('')
const translateError = ref('')
const translateBusy = ref(false)

async function loadProviders() {
  providers.value = await useAuthFetch<Record<string, boolean>>('/api/v1/ai/providers/')
}

async function pollTask(taskId: string): Promise<{ ok: boolean; result?: string; error?: string }> {
  for (let i = 0; i < 30; i++) {
    const status = await useAuthFetch<any>(`/api/v1/ai/tasks/${taskId}/`)
    if (status.status === 'SUCCESS' || status.status === 'FAILURE' || 'ok' in status) return status
    await new Promise((r) => setTimeout(r, 1000))
  }
  return { ok: false, error: 'Timed out waiting for a result.' }
}

async function runGenerate() {
  if (!prompt.value) return
  genBusy.value = true
  genResult.value = ''
  genError.value = ''
  try {
    const { task_id } = await useAuthFetch<{ task_id: string }>('/api/v1/ai/generate/', {
      method: 'POST',
      body: { prompt: prompt.value, provider: providerChoice.value },
    })
    const result = await pollTask(task_id)
    if (result.ok) genResult.value = result.result || ''
    else genError.value = result.error || 'Generation failed.'
  } catch {
    genError.value = 'Request failed.'
  } finally {
    genBusy.value = false
  }
}

async function runTranslate() {
  if (!translateText.value) return
  translateBusy.value = true
  translateResult.value = ''
  translateError.value = ''
  try {
    const { task_id } = await useAuthFetch<{ task_id: string }>('/api/v1/ai/translate/', {
      method: 'POST',
      body: {
        text: translateText.value,
        source_locale: sourceLocale.value,
        target_locale: targetLocale.value,
        provider: providerChoice.value,
      },
    })
    const result = await pollTask(task_id)
    if (result.ok) translateResult.value = result.result || ''
    else translateError.value = result.error || 'Translation failed.'
  } catch {
    translateError.value = 'Request failed.'
  } finally {
    translateBusy.value = false
  }
}

onMounted(loadProviders)
useSeoMeta({ title: 'AI Tools — CMS Admin' })
</script>

<template>
  <div class="max-w-2xl">
    <h1 class="text-2xl font-black">AI Tools</h1>

    <div class="mt-3 flex flex-wrap gap-2">
      <span
        v-for="(connected, name) in providers"
        :key="name"
        class="rounded-full px-3 py-1 text-xs font-semibold capitalize"
        :style="connected ? 'background: var(--success-bg); color: var(--success)' : 'background: var(--surface-2); color: var(--text-faint)'"
      >
        {{ name }} · {{ connected ? 'connected' : 'not configured' }}
      </span>
    </div>
    <p class="mt-1 text-xs" style="color: var(--text-faint)">
      Configure API keys under <NuxtLink to="/admin/settings" class="text-primary">Settings</NuxtLink> (category "ai").
    </p>

    <v-select
      v-model="providerChoice"
      :items="Object.keys(providers)"
      label="Provider"
      hide-details
      density="compact"
      class="mt-4"
      style="max-width: 14rem"
    />

    <div class="mt-6 rounded-lg border p-5" style="border-color: var(--border); background: var(--surface)">
      <h2 class="font-bold">Generate content</h2>
      <v-textarea v-model="prompt" label="Prompt" rows="3" hide-details density="compact" class="mt-2" />
      <v-btn class="mt-3" color="primary" :loading="genBusy" @click="runGenerate">Generate</v-btn>
      <p v-if="genError" class="mt-2 text-sm" style="color: var(--error)">{{ genError }}</p>
      <p v-if="genResult" class="mt-3 whitespace-pre-wrap rounded p-3 text-sm" style="background: var(--surface-2)">
        {{ genResult }}
      </p>
    </div>

    <div class="mt-6 rounded-lg border p-5" style="border-color: var(--border); background: var(--surface)">
      <h2 class="font-bold">Translate content</h2>
      <v-textarea v-model="translateText" label="Text" rows="3" hide-details density="compact" class="mt-2" />
      <div class="mt-2 flex gap-3">
        <v-select v-model="sourceLocale" :items="['en', 'km']" label="From" hide-details density="compact" style="max-width: 8rem" />
        <v-select v-model="targetLocale" :items="['en', 'km']" label="To" hide-details density="compact" style="max-width: 8rem" />
      </div>
      <v-btn class="mt-3" color="primary" :loading="translateBusy" @click="runTranslate">Translate</v-btn>
      <p v-if="translateError" class="mt-2 text-sm" style="color: var(--error)">{{ translateError }}</p>
      <p v-if="translateResult" class="mt-3 whitespace-pre-wrap rounded p-3 text-sm" style="background: var(--surface-2)">
        {{ translateResult }}
      </p>
    </div>
  </div>
</template>
