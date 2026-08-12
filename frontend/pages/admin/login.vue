<script setup lang="ts">
const email = ref('')
const password = ref('')
const code = ref('')
const error = ref('')
const loading = ref(false)
const auth = useAuthStore()
const router = useRouter()
const config = useRuntimeConfig()

const pendingToken = ref<string | null>(null)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const result = await auth.login(email.value, password.value)
    if (result.requiresTwoFactor) {
      pendingToken.value = result.pendingToken
    } else {
      await router.push('/admin/pages')
    }
  } catch {
    error.value = 'Invalid email or password.'
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
    await router.push('/admin/pages')
  } catch {
    error.value = 'Invalid code — check your authenticator app or use a recovery code.'
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
  <div class="mx-auto mt-24 max-w-sm px-6">
    <h1 class="text-2xl font-black">Admin Login</h1>

    <form v-if="!pendingToken" class="mt-6 space-y-4" @submit.prevent="submit">
      <v-text-field v-model="email" label="Email" type="email" required />
      <v-text-field v-model="password" label="Password" type="password" required />
      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
      <v-btn type="submit" color="primary" block :loading="loading">Log in</v-btn>

      <div class="flex items-center gap-3 pt-2 text-xs text-gray-400">
        <div class="h-px flex-1 bg-gray-200" />
        or
        <div class="h-px flex-1 bg-gray-200" />
      </div>
      <a :href="socialLoginUrl('google')" class="block rounded border px-3 py-2 text-center text-sm font-semibold">
        Continue with Google
      </a>
      <a :href="socialLoginUrl('facebook')" class="block rounded border px-3 py-2 text-center text-sm font-semibold">
        Continue with Facebook
      </a>
    </form>

    <form v-else class="mt-6 space-y-4" @submit.prevent="submitCode">
      <p class="text-sm text-gray-500">Enter the 6-digit code from your authenticator app, or a recovery code.</p>
      <v-text-field v-model="code" label="Code" required />
      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
      <v-btn type="submit" color="primary" block :loading="loading">Verify</v-btn>
    </form>
  </div>
</template>
