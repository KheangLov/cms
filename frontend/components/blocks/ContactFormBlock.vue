<script setup lang="ts">
interface Props {
  block: { props: Record<string, any> }
  locale?: string
}
const props = defineProps<Props>()

function t(field: string): string {
  const value = props.block.props[field]
  if (value && typeof value === 'object') {
    return value[props.locale || 'en'] ?? value.en ?? ''
  }
  return value ?? ''
}

const config = useRuntimeConfig()
const apiBase = (import.meta.server ? config.apiBaseInternal : config.public.apiBase) as string
const { t: $t } = useI18n()

const name = ref('')
const email = ref('')
const message = ref('')
const status = ref<'idle' | 'sending' | 'sent' | 'error'>('idle')
const errorMessage = ref('')

async function submit() {
  status.value = 'sending'
  errorMessage.value = ''
  try {
    await $fetch('/api/v1/contact-submissions/', {
      method: 'POST',
      baseURL: apiBase,
      body: { name: name.value, email: email.value, message: message.value },
    })
    status.value = 'sent'
    name.value = ''
    email.value = ''
    message.value = ''
  } catch (err: any) {
    status.value = 'error'
    errorMessage.value = err?.data?.email?.[0] || err?.data?.detail || $t('publicContactForm.error')
  }
}
</script>

<template>
  <section class="mx-auto max-w-xl px-6 py-10">
    <h2 v-if="t('heading')" class="text-2xl font-black">{{ t('heading') }}</h2>
    <p v-if="t('subheading')" class="mt-1 text-sm" style="color: var(--text-secondary)">{{ t('subheading') }}</p>

    <div v-if="status === 'sent'" class="bento-card mt-5 p-5 text-center" style="background: var(--success-bg); color: var(--success)">
      <Icon name="solar:check-circle-bold-duotone" size="1.5rem" />
      <p class="mt-2 text-sm font-semibold">{{ $t('publicContactForm.sentMessage') }}</p>
    </div>
    <form v-else class="mt-5 space-y-3" @submit.prevent="submit">
      <div>
        <label class="block text-xs font-semibold">{{ $t('publicContactForm.nameLabel') }}</label>
        <input v-model="name" required class="bento-input mt-1" />
      </div>
      <div>
        <label class="block text-xs font-semibold">{{ $t('publicContactForm.emailLabel') }}</label>
        <input v-model="email" type="email" required class="bento-input mt-1" />
      </div>
      <div>
        <label class="block text-xs font-semibold">{{ $t('publicContactForm.messageLabel') }}</label>
        <textarea v-model="message" required rows="4" class="bento-input mt-1" />
      </div>
      <p v-if="status === 'error'" class="text-xs" style="color: var(--error)">{{ errorMessage }}</p>
      <v-btn color="primary" block type="submit" :loading="status === 'sending'">
        {{ t('submitLabel') || $t('publicContactForm.submitLabel') }}
      </v-btn>
    </form>
  </section>
</template>
