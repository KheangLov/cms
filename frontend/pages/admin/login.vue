<script setup lang="ts">
const email = ref('')
const password = ref('')
const code = ref('')
const error = ref('')
const loading = ref(false)
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const config = useRuntimeConfig()
const { t } = useI18n()

const pendingToken = ref<string | null>(null)

function destination(): string {
  const redirect = route.query.redirect
  return typeof redirect === 'string' && redirect.startsWith('/admin') ? redirect : '/admin'
}

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const result = await auth.login(email.value, password.value)
    if (result.requiresTwoFactor) {
      pendingToken.value = result.pendingToken
    } else {
      await router.push(destination())
    }
  } catch {
    error.value = t('auth.invalidCredentials')
  } finally {
    loading.value = false
  }
}

async function submitCode() {
  if (!pendingToken.value) return
  error.value = ''
  loading.value = true
  try {
    await auth.verifyTwoFactor(pendingToken.value, code.value)
    await router.push(destination())
  } catch {
    error.value = t('auth.invalidCode')
  } finally {
    loading.value = false
  }
}

function socialLoginUrl(provider: string): string {
  // §5.6 — real end-to-end sign-in needs a Google/Facebook OAuth app's
  // credentials configured on the backend; the link itself is always live.
  return `${config.public.apiBase}/accounts/${provider}/login/`
}

useSeoMeta({ title: 'Admin Login — CMS Platform' })
</script>

<template>
  <div class="flex min-h-screen items-center justify-center px-6">
    <div
      class="bento-card w-full max-w-sm p-6"
      style="background: var(--glass-bg); backdrop-filter: blur(1.25rem) saturate(160%); border-color: var(--glass-border)"
    >
      <div class="flex flex-col items-center gap-3 text-center">
        <EmberLogo size="2.75rem" />
        <div>
          <div class="text-lg font-black gradient-text">Ember CMS</div>
          <h1 class="mt-0.5 text-sm font-semibold" style="color: var(--text-secondary)">{{ $t('auth.loginTitle') }}</h1>
        </div>
      </div>

      <form v-if="!pendingToken" class="mt-6 space-y-4" @submit.prevent="submit">
        <v-text-field v-model="email" :label="$t('auth.emailLabel')" type="email" required>
          <template #prepend-inner><Icon name="solar:letter-bold-duotone" size="1.1rem" /></template>
        </v-text-field>
        <v-text-field v-model="password" :label="$t('auth.passwordLabel')" type="password" required>
          <template #prepend-inner><Icon name="solar:lock-password-bold-duotone" size="1.1rem" /></template>
        </v-text-field>
        <p v-if="error" class="text-sm" style="color: var(--error)">{{ error }}</p>
        <v-btn type="submit" color="primary" block :loading="loading">{{ $t('auth.loginButton') }}</v-btn>

        <div class="flex items-center gap-3 pt-2 text-xs" style="color: var(--text-faint)">
          <div class="h-px flex-1" style="background: var(--border)" />
          {{ $t('auth.orContinueWith') }}
          <div class="h-px flex-1" style="background: var(--border)" />
        </div>
        <a
          :href="socialLoginUrl('google')"
          class="flex items-center justify-center gap-2 border px-3 py-2 text-sm font-semibold no-underline"
          style="border-color: var(--border); border-radius: var(--radius-full); color: var(--text-primary)"
        >
          <Icon name="solar:global-bold-duotone" size="1.05rem" />
          {{ $t('auth.continueWithGoogle') }}
        </a>
        <a
          :href="socialLoginUrl('facebook')"
          class="flex items-center justify-center gap-2 border px-3 py-2 text-sm font-semibold no-underline"
          style="border-color: var(--border); border-radius: var(--radius-full); color: var(--text-primary)"
        >
          <Icon name="solar:chat-round-bold-duotone" size="1.05rem" />
          {{ $t('auth.continueWithFacebook') }}
        </a>
      </form>

      <form v-else class="mt-6 space-y-4" @submit.prevent="submitCode">
        <p class="text-sm" style="color: var(--text-secondary)">
          {{ $t('auth.twoFactorHint') }}
        </p>
        <v-text-field v-model="code" :label="$t('auth.codeLabel')" required>
          <template #prepend-inner><Icon name="solar:key-bold-duotone" size="1.1rem" /></template>
        </v-text-field>
        <p v-if="error" class="text-sm" style="color: var(--error)">{{ error }}</p>
        <v-btn type="submit" color="primary" block :loading="loading">{{ $t('auth.verifyButton') }}</v-btn>
      </form>
    </div>
  </div>
</template>
