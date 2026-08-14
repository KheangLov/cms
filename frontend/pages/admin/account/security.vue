<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

const auth = useAuthStore()
const { confirm } = useConfirmDialog()
const { t } = useI18n()

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
    error.value = t('account.twoFactorSetupError')
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
    error.value = t('account.twoFactorInvalidCode')
  } finally {
    loading.value = false
  }
}

async function disable() {
  const ok = await confirm({
    title: t('account.disable2faTitle'),
    message: t('account.disable2faMessage'),
    confirmLabel: t('account.disable'),
    danger: true,
  })
  if (!ok) return
  await useAuthFetch('/api/v1/auth/2fa/disable/', { method: 'POST' })
  if (auth.user) auth.user.is_2fa_enabled = false
  step.value = 'idle'
}

useSeoMeta({ title: 'Account & Security — CMS Admin' })
</script>

<template>
  <div class="max-w-lg">
    <h1 class="text-2xl font-black">{{ $t('account.accountSecurity') }}</h1>
    <p class="mt-1 text-sm" style="color: var(--text-secondary)">{{ auth.user?.email }}</p>

    <div class="bento-card mt-6 p-5">
      <div class="flex items-center gap-2">
        <span
          class="bento-tile__icon"
          :class="auth.user?.is_2fa_enabled || step === 'confirmed' ? 'bento-tile__icon--success' : 'bento-tile__icon--ember'"
          style="width: 2rem; height: 2rem; font-size: 1.1rem"
        >
          <Icon name="solar:shield-check-bold-duotone" />
        </span>
        <h2 class="font-bold">{{ $t('account.twoFactor') }}</h2>
      </div>

      <template v-if="step === 'confirmed'">
        <p class="mt-3 text-sm" style="color: var(--success)">{{ $t('account.twoFactorEnabledSaveCodes') }}</p>
        <ul class="mt-3 grid grid-cols-2 gap-1 rounded p-3 font-mono text-sm" style="background: var(--surface-2)">
          <li v-for="rc in recoveryCodes" :key="rc" class="flex items-center gap-1.5">
            <Icon name="solar:key-bold-duotone" size="0.9rem" style="color: var(--text-faint)" />
            {{ rc }}
          </li>
        </ul>
      </template>

      <template v-else-if="auth.user?.is_2fa_enabled">
        <p class="mt-3 text-sm" style="color: var(--success)">{{ $t('account.twoFactorEnabled') }}</p>
        <v-btn class="mt-3" color="error" variant="tonal" @click="disable">
          <Icon name="solar:shield-warning-bold-duotone" size="1.05rem" class="mr-1.5" />
          {{ $t('account.disable2fa') }}
        </v-btn>
      </template>

      <template v-else-if="step === 'idle'">
        <p class="mt-3 text-sm" style="color: var(--text-secondary)">
          {{ $t('account.twoFactorNotEnabled') }}
        </p>
        <v-btn class="mt-3" color="primary" :loading="loading" @click="startSetup">
          <Icon name="solar:shield-check-bold-duotone" size="1.05rem" class="mr-1.5" />
          {{ $t('account.enable2fa') }}
        </v-btn>
      </template>

      <template v-else-if="step === 'setup'">
        <p class="mt-3 text-sm" style="color: var(--text-secondary)">
          {{ $t('account.scanQr') }}
        </p>
        <div class="mt-3 inline-flex rounded-lg p-2" style="background: #fff">
          <img :src="qrCode" alt="2FA QR code" class="h-40 w-40" />
        </div>
        <p class="mt-2 flex items-center gap-1.5 text-xs" style="color: var(--text-faint)">
          <Icon name="solar:qr-code-bold-duotone" size="0.95rem" />
          {{ $t('account.cantScan') }} <code>{{ secret }}</code>
        </p>
        <v-text-field v-model="code" :label="$t('account.sixDigitCode')" hide-details density="compact" class="mt-3" style="max-width: 12rem" />
        <p v-if="error" class="mt-2 text-sm" style="color: var(--error)">{{ error }}</p>
        <v-btn class="mt-3" color="primary" :loading="loading" @click="confirmSetup">
          <Icon name="solar:check-circle-bold-duotone" size="1.05rem" class="mr-1.5" />
          {{ $t('common.confirm') }}
        </v-btn>
      </template>
    </div>
  </div>
</template>
