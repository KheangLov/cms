<script setup lang="ts">
// Lands here after Django/allauth completes a Google/Facebook OAuth flow and
// redirects back with a one-time exchange code (apps/users/social.py). Not
// live-testable without real OAuth app credentials — see CMS_BUILD_PROMPT.md §5.6.
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { t } = useI18n()
const error = ref('')

onMounted(async () => {
  const code = route.query.code as string | undefined
  if (!code) {
    error.value = t('auth.missingExchangeCode')
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
    error.value = t('auth.socialLoginExpired')
  }
})

useSeoMeta({ title: 'Signing in… — CMS Admin' })
</script>

<template>
  <div class="mx-auto mt-24 max-w-sm px-6 text-center">
    <p v-if="error" class="flex items-center justify-center gap-1.5 text-sm" style="color: var(--error)">
      <Icon name="solar:close-circle-bold-duotone" size="1.1rem" />
      {{ error }}
    </p>
    <div v-else class="flex items-center justify-center gap-2 text-sm" style="color: var(--text-faint)">
      <v-progress-circular size="18" width="2" indeterminate color="primary" />
      {{ $t('auth.signingIn') }}
    </div>
  </div>
</template>
