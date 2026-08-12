<script setup lang="ts">
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const auth = useAuthStore()
const router = useRouter()

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    await router.push('/admin/pages')
  } catch {
    error.value = 'Invalid email or password.'
  } finally {
    loading.value = false
  }
}

useSeoMeta({ title: 'Admin Login — CMS Platform' })
</script>

<template>
  <div class="mx-auto mt-24 max-w-sm px-6">
    <h1 class="text-2xl font-black">Admin Login</h1>
    <form class="mt-6 space-y-4" @submit.prevent="submit">
      <v-text-field v-model="email" label="Email" type="email" required />
      <v-text-field v-model="password" label="Password" type="password" required />
      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
      <v-btn type="submit" color="primary" block :loading="loading">Log in</v-btn>
    </form>
  </div>
</template>
