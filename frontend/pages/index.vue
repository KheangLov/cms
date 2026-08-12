<script setup lang="ts">
interface HealthCheck {
  ok: boolean
  detail: string
}
interface HealthResponse {
  status: string
  checks: Record<string, HealthCheck>
}

const config = useRuntimeConfig()
// SSR runs inside the frontend container and must reach the backend via the Docker
// network; the browser reaches it via the published host port. See nuxt.config.ts.
const apiBase = import.meta.server ? config.apiBaseInternal : config.public.apiBase

const { data: health } = await useFetch<HealthResponse>('/api/v1/health/', {
  baseURL: apiBase,
})

const { locale, locales, setLocale } = useI18n()
const colorMode = useColorMode()

useSeoMeta({
  title: 'CMS Platform — Phase 0',
  description: 'Infra skeleton: every service wired up and talking to each other.',
})
</script>

<template>
  <main class="mx-auto max-w-3xl px-6 py-16">
    <span class="text-xs font-bold uppercase tracking-wide text-[var(--color-text-faint,var(--text-faint))]">
      CMS platform
    </span>
    <h1 class="gradient-text mt-2 text-4xl font-black">Phase 0 — infra skeleton</h1>
    <p class="mt-2 text-[color:var(--text-secondary)]">
      Every service in the stack, wired up and talking to each other. Nothing product-shaped
      yet — that starts at Phase 1.
    </p>

    <section
      class="mt-8 rounded-lg border p-4"
      :class="health?.status === 'healthy' ? 'border-success' : 'border-error'"
    >
      <h2 class="font-bold">
        Backend status: {{ health?.status ?? 'unreachable' }}
      </h2>
      <ul class="mt-3 space-y-1 text-sm">
        <li v-for="(check, name) in health?.checks" :key="name">
          {{ check.ok ? '✅' : '❌' }} <strong>{{ name }}</strong> — {{ check.detail }}
        </li>
      </ul>
    </section>

    <section class="mt-8 flex flex-wrap items-center gap-3">
      <v-btn color="primary" rounded="sm">Vuetify button</v-btn>
      <button class="rounded-full bg-primary px-4 py-2 text-sm font-bold text-white">
        Tailwind button
      </button>
      <v-btn variant="tonal" color="primary" @click="colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'">
        Toggle {{ colorMode.value === 'dark' ? 'light' : 'dark' }} mode
      </v-btn>
    </section>

    <section class="mt-6 flex gap-2">
      <button
        v-for="l in locales"
        :key="typeof l === 'string' ? l : l.code"
        class="rounded-full border px-3 py-1 text-sm"
        :class="{ 'bg-primary text-white': locale === (typeof l === 'string' ? l : l.code) }"
        @click="setLocale(typeof l === 'string' ? l : l.code)"
      >
        {{ typeof l === 'string' ? l : l.name }}
      </button>
    </section>
  </main>
</template>
