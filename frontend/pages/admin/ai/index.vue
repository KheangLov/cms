<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

const { t } = useI18n()
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
  return { ok: false, error: t('aiAdmin.timedOut') }
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
    else genError.value = result.error || t('aiAdmin.generationFailed')
  } catch {
    genError.value = t('aiAdmin.requestFailed')
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
    else translateError.value = result.error || t('aiAdmin.translationFailed')
  } catch {
    translateError.value = t('aiAdmin.requestFailed')
  } finally {
    translateBusy.value = false
  }
}

onMounted(loadProviders)
useSeoMeta({ title: 'AI Tools — CMS Admin' })
</script>

<template>
  <div class="max-w-4xl">
    <h1 class="text-2xl font-black">{{ $t('aiAdmin.title') }}</h1>

    <div class="mt-3 flex flex-wrap gap-2">
      <span
        v-for="(connected, name) in providers"
        :key="name"
        class="flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold capitalize"
        :style="connected ? 'background: var(--success-bg); color: var(--success)' : 'background: var(--surface-2); color: var(--text-faint)'"
      >
        <Icon :name="connected ? 'solar:check-circle-bold-duotone' : 'solar:close-circle-bold-duotone'" size="1rem" />
        {{ name }} · {{ connected ? $t('aiAdmin.connected') : $t('aiAdmin.notConfigured') }}
      </span>
    </div>
    <p class="mt-1 text-xs" style="color: var(--text-faint)">
      {{ $t('aiAdmin.configureHintPrefix') }} <NuxtLink to="/admin/settings" class="text-primary">{{ $t('nav.settings') }}</NuxtLink> {{ $t('aiAdmin.configureHintSuffix') }}
    </p>

    <v-select
      v-model="providerChoice"
      :items="Object.keys(providers)"
      :label="$t('aiAdmin.provider')"
      hide-details
      density="compact"
      class="mt-4"
      style="max-width: 14rem"
    />

    <div class="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
      <div class="bento-card p-5">
        <div class="flex items-center gap-2">
          <span class="bento-tile__icon bento-tile__icon--ember" style="width: 2rem; height: 2rem; font-size: 1.1rem">
            <Icon name="solar:magic-stick-3-bold-duotone" />
          </span>
          <h2 class="font-bold">{{ $t('aiAdmin.generateContent') }}</h2>
        </div>
        <v-textarea v-model="prompt" :label="$t('aiAdmin.prompt')" rows="3" hide-details density="compact" class="mt-3" />
        <v-btn class="mt-3" color="primary" :loading="genBusy" @click="runGenerate">
          <Icon name="solar:magic-stick-3-bold-duotone" size="1.05rem" class="mr-1.5" />
          {{ $t('aiAdmin.generate') }}
        </v-btn>
        <p v-if="genError" class="mt-2 text-sm" style="color: var(--error)">{{ genError }}</p>
        <p v-if="genResult" class="mt-3 whitespace-pre-wrap rounded p-3 text-sm" style="background: var(--surface-2)">
          {{ genResult }}
        </p>
      </div>

      <div class="bento-card p-5">
        <div class="flex items-center gap-2">
          <span class="bento-tile__icon bento-tile__icon--info" style="width: 2rem; height: 2rem; font-size: 1.1rem">
            <Icon name="solar:translation-2-bold-duotone" />
          </span>
          <h2 class="font-bold">{{ $t('aiAdmin.translateContent') }}</h2>
        </div>
        <v-textarea v-model="translateText" :label="$t('aiAdmin.text')" rows="3" hide-details density="compact" class="mt-3" />
        <div class="mt-2 flex gap-3">
          <v-select v-model="sourceLocale" :items="['en', 'km']" :label="$t('aiAdmin.from')" hide-details density="compact" style="max-width: 8rem" />
          <v-select v-model="targetLocale" :items="['en', 'km']" :label="$t('aiAdmin.to')" hide-details density="compact" style="max-width: 8rem" />
        </div>
        <v-btn class="mt-3" color="primary" :loading="translateBusy" @click="runTranslate">
          <Icon name="solar:translation-2-bold-duotone" size="1.05rem" class="mr-1.5" />
          {{ $t('aiAdmin.translate') }}
        </v-btn>
        <p v-if="translateError" class="mt-2 text-sm" style="color: var(--error)">{{ translateError }}</p>
        <p v-if="translateResult" class="mt-3 whitespace-pre-wrap rounded p-3 text-sm" style="background: var(--surface-2)">
          {{ translateResult }}
        </p>
      </div>
    </div>
  </div>
</template>
