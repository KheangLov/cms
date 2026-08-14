<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

const auth = useAuthStore()
const colorMode = useColorMode()
const { locale, t } = useI18n()

const firstName = ref(auth.user?.first_name || '')
const lastName = ref(auth.user?.last_name || '')
const email = ref(auth.user?.email || '')
const localePreference = ref(auth.user?.locale_preference || 'en')
const themePreference = ref(auth.user?.theme_preference || 'light')

const avatarFile = ref<File | null>(null)
const avatarPreview = ref<string | null>(auth.user?.avatar || null)
const fileInput = ref<HTMLInputElement | null>(null)

const saving = ref(false)
const saved = ref(false)
const error = ref('')

function initials(): string {
  const f = firstName.value?.[0] || auth.user?.email?.[0] || ''
  const l = lastName.value?.[0] || ''
  return (f + l).toUpperCase() || '?'
}

function pickAvatar() {
  fileInput.value?.click()
}

function onAvatarSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  avatarFile.value = file
  avatarPreview.value = URL.createObjectURL(file)
}

async function save() {
  saving.value = true
  saved.value = false
  error.value = ''
  try {
    let body: FormData | Record<string, unknown>
    if (avatarFile.value) {
      // A File anywhere in the payload means multipart — mirrors the pattern
      // media/index.vue already uses for uploads. useAuthFetch/ofetch detects
      // FormData automatically and skips setting Content-Type itself, so the
      // browser can add the multipart boundary.
      const form = new FormData()
      form.append('first_name', firstName.value)
      form.append('last_name', lastName.value)
      form.append('email', email.value)
      form.append('locale_preference', localePreference.value)
      form.append('theme_preference', themePreference.value)
      form.append('avatar', avatarFile.value)
      body = form
    } else {
      body = {
        first_name: firstName.value,
        last_name: lastName.value,
        email: email.value,
        locale_preference: localePreference.value,
        theme_preference: themePreference.value,
      }
    }
    const updated = await useAuthFetch<typeof auth.user>('/api/v1/auth/me/', { method: 'PATCH', body })
    auth.user = updated
    avatarFile.value = null
    // Preferences only take effect live if we also flip colorMode/i18n's own
    // state here — otherwise the field would silently do nothing until the
    // next full page load.
    colorMode.preference = themePreference.value
    locale.value = localePreference.value
    saved.value = true
    setTimeout(() => (saved.value = false), 2000)
  } catch (e: any) {
    error.value = e?.data?.email?.[0] || e?.data?.detail || t('account.couldNotSaveChanges')
  } finally {
    saving.value = false
  }
}

useSeoMeta({ title: 'Profile — CMS Admin' })
</script>

<template>
  <div class="max-w-xl">
    <h1 class="text-2xl font-black">{{ $t('account.profileTitle') }}</h1>
    <p class="mt-1 text-sm" style="color: var(--text-secondary)">
      {{ $t('account.profileSubtitle') }}
    </p>

    <div class="bento-card mt-6 p-6">
      <div class="flex items-center gap-4">
        <button
          class="relative flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-full text-lg font-bold"
          style="background: var(--gradient-primary); color: #fff"
          :title="$t('account.changeAvatar')"
          @click="pickAvatar"
        >
          <img v-if="avatarPreview" :src="avatarPreview" :alt="$t('account.changeAvatar')" class="h-full w-full object-cover" />
          <span v-else>{{ initials() }}</span>
        </button>
        <div>
          <v-btn variant="tonal" size="small" @click="pickAvatar">
            <Icon name="solar:camera-bold-duotone" size="1rem" class="mr-1.5" />
            {{ $t('account.changeAvatar') }}
          </v-btn>
          <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onAvatarSelected" />
        </div>
      </div>

      <div class="mt-6 flex gap-3">
        <v-text-field v-model="firstName" :label="$t('account.firstName')" hide-details density="compact" />
        <v-text-field v-model="lastName" :label="$t('account.lastName')" hide-details density="compact" />
      </div>
      <v-text-field v-model="email" :label="$t('common.email')" type="email" hide-details density="compact" class="mt-3">
        <template #prepend-inner><Icon name="solar:letter-bold-duotone" size="1.1rem" /></template>
      </v-text-field>

      <div class="mt-3 flex gap-3">
        <v-select
          v-model="localePreference"
          :items="[
            { title: 'English', value: 'en' },
            { title: 'ខ្មែរ (Khmer)', value: 'km' },
          ]"
          :label="$t('common.language')"
          hide-details
          density="compact"
        />
        <v-select
          v-model="themePreference"
          :items="[
            { title: $t('common.lightTheme'), value: 'light' },
            { title: $t('common.darkTheme'), value: 'dark' },
          ]"
          :label="$t('common.theme')"
          hide-details
          density="compact"
        />
      </div>

      <p v-if="error" class="mt-3 text-sm" style="color: var(--error)">{{ error }}</p>

      <div class="mt-5 flex items-center gap-3">
        <v-btn color="primary" variant="elevated" :loading="saving" @click="save">{{ $t('common.saveChanges') }}</v-btn>
        <span v-if="saved" class="flex items-center gap-1 text-sm" style="color: var(--success)">
          <Icon name="solar:check-circle-bold-duotone" size="1rem" />
          {{ $t('common.saved') }}
        </span>
      </div>
    </div>
  </div>
</template>
