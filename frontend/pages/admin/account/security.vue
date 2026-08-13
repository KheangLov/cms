<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

const auth = useAuthStore()

const step = ref<'idle' | 'setup' | 'confirmed'>('idle')
const qrCode = ref('')
const secret = ref('')
const code = ref('')
const recoveryCodes = ref<string[]>([])
const error = ref('')
const loading = ref(false)

async function startSetup() {
  error.value = ''
  loading.value = true
  try {
    const resp = await useAuthFetch<{ secret: string; qr_code: string }>('/api/v1/auth/2fa/setup/', { method: 'POST' })
    qrCode.value = resp.qr_code
    secret.value = resp.secret
    step.value = 'setup'
  } catch {
    error.value = 'Could not start 2FA setup.'
  } finally {
    loading.value = false
  }
}

async function confirmSetup() {
  error.value = ''
  loading.value = true
  try {
    const resp = await useAuthFetch<{ recovery_codes: string[] }>('/api/v1/auth/2fa/confirm/', {
      method: 'POST',
      body: { code: code.value },
    })
    recoveryCodes.value = resp.recovery_codes
    step.value = 'confirmed'
    if (auth.user) auth.user.is_2fa_enabled = true
  } catch {
    error.value = 'Invalid code — check your authenticator app.'
  } finally {
    loading.value = false
  }
}

async function disable() {
  if (!confirm('Disable two-factor authentication?')) return
  await useAuthFetch('/api/v1/auth/2fa/disable/', { method: 'POST' })
  if (auth.user) auth.user.is_2fa_enabled = false
  step.value = 'idle'
}

useSeoMeta({ title: 'Account & Security — CMS Admin' })
</script>

<template>
  <div class="max-w-lg">
    <h1 class="text-2xl font-black">Account &amp; security</h1>
    <p class="mt-1 text-sm" style="color: var(--text-secondary)">{{ auth.user?.email }}</p>

    <div class="mt-6 rounded-lg border p-5" style="border-color: var(--border); background: var(--surface)">
      <h2 class="font-bold">Two-factor authentication</h2>

      <template v-if="step === 'confirmed'">
        <p class="mt-2 text-sm" style="color: var(--success)">2FA is now enabled. Save these recovery codes somewhere safe — each works once, and this is the only time they're shown.</p>
        <ul class="mt-3 grid grid-cols-2 gap-1 rounded p-3 font-mono text-sm" style="background: var(--surface-2)">
          <li v-for="rc in recoveryCodes" :key="rc">{{ rc }}</li>
        </ul>
      </template>

      <template v-else-if="auth.user?.is_2fa_enabled">
        <p class="mt-2 text-sm" style="color: var(--success)">2FA is enabled on your account.</p>
        <v-btn class="mt-3" color="error" variant="tonal" @click="disable">Disable 2FA</v-btn>
      </template>

      <template v-else-if="step === 'idle'">
        <p class="mt-2 text-sm" style="color: var(--text-secondary)">
          Not enabled. Add an authenticator app for an extra layer of login security.
        </p>
        <v-btn class="mt-3" color="primary" :loading="loading" @click="startSetup">Enable 2FA</v-btn>
      </template>

      <template v-else-if="step === 'setup'">
        <p class="mt-2 text-sm" style="color: var(--text-secondary)">
          Scan this with your authenticator app, then enter the 6-digit code it shows.
        </p>
        <img :src="qrCode" alt="2FA QR code" class="mt-3 h-40 w-40 rounded border" style="border-color: var(--border)" />
        <p class="mt-2 text-xs" style="color: var(--text-faint)">Can't scan? Enter manually: <code>{{ secret }}</code></p>
        <v-text-field v-model="code" label="6-digit code" hide-details density="compact" class="mt-3" style="max-width: 12rem" />
        <p v-if="error" class="mt-2 text-sm" style="color: var(--error)">{{ error }}</p>
        <v-btn class="mt-3" color="primary" :loading="loading" @click="confirmSetup">Confirm</v-btn>
      </template>
    </div>
  </div>
</template>
