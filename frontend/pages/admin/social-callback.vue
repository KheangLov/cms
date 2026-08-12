<script setup lang="ts">
// Lands here after Django/allauth completes a Google/Facebook OAuth flow and
// redirects back with a one-time exchange code (apps/users/social.py). Not
// live-testable without real OAuth app credentials — see CMS_BUILD_PROMPT.md §5.6.
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const error = ref('')

onMounted(async () => {
  const code = route.query.code as string | undefined
  if (!code) {
    error.value = 'Missing exchange code.'
    return
  }
  try {
    const config = useRuntimeConfig()
    const data = await $fetch<{ access: string; user: any }>('/api/v1/auth/social/exchange/', {
      baseURL: config.public.apiBase as string,
      method: 'POST',
      body: { code },
      credentials: 'include',
    })
    auth.accessToken = data.access
    auth.user = data.user
    await router.push('/admin/pages')
  } catch {
    error.value = 'That sign-in link expired or was already used — try signing in again.'
  }
})

useSeoMeta({ title: 'Signing in… — CMS Admin' })
</script>

<template>
  <div class="mx-auto mt-24 max-w-sm px-6 text-center">
    <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
    <p v-else class="text-sm text-gray-400">Signing you in…</p>
  </div>
</template>
