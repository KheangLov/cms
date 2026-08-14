<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

const { confirm } = useConfirmDialog()
const { t } = useI18n()

interface SettingRow {
  id: number
  key: string
  value: unknown
  category: string
  is_secret: boolean
  description: string
  has_value?: boolean
}

const dialog = ref(false)
const editing = ref<SettingRow | null>(null)
const form = reactive({ key: '', valueText: '', category: 'general', is_secret: false, description: '' })

const search = ref('')

const { items: settings, loading, loadingMore, hasMore, load, loadMore } = useInfiniteList<SettingRow>(() => {
  const params = new URLSearchParams()
  if (search.value) params.set('search', search.value)
  return `/api/v1/settings/?${params}`
})
const sentinel = useInfiniteScrollSentinel(loadMore)

const grouped = computed(() => {
  const groups: Record<string, SettingRow[]> = {}
  for (const s of settings.value) {
    ;(groups[s.category] ||= []).push(s)
  }
  return groups
})

watch(search, useDebounceFn(load, 300))

function openCreate() {
  editing.value = null
  Object.assign(form, { key: '', valueText: '', category: 'general', is_secret: false, description: '' })
  dialog.value = true
}

function openEdit(setting: SettingRow) {
  editing.value = setting
  Object.assign(form, {
    key: setting.key,
    valueText: setting.is_secret ? '' : typeof setting.value === 'string' ? setting.value : JSON.stringify(setting.value),
    category: setting.category,
    is_secret: setting.is_secret,
    description: setting.description,
  })
  dialog.value = true
}

function parseValue(text: string): unknown {
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

async function save() {
  const body: Record<string, unknown> = {
    key: form.key,
    category: form.category,
    is_secret: form.is_secret,
    description: form.description,
  }
  // For secrets, an empty box means "leave unchanged" — omit `value` entirely so the
  // backend's partial-update path (settings_app/serializers.py) keeps the existing one.
  if (form.valueText !== '' || !editing.value) {
    body.value = parseValue(form.valueText)
  }
  if (editing.value) {
    // SettingViewSet sets lookup_field = "key", so detail routes are /settings/<key>/
    // — not /settings/<id>/, which 404s. The key input is disabled while editing, so
    // the original key is always the right lookup here.
    await useAuthFetch(`/api/v1/settings/${encodeURIComponent(editing.value.key)}/`, { method: 'PATCH', body })
  } else {
    await useAuthFetch('/api/v1/settings/', { method: 'POST', body })
  }
  dialog.value = false
  await load()
}

async function remove(setting: SettingRow) {
  if (!(await confirm({ message: t('settingsAdmin.deleteConfirm', { key: setting.key }), danger: true }))) return
  await useAuthFetch(`/api/v1/settings/${encodeURIComponent(setting.key)}/`, { method: 'DELETE' })
  await load()
}

onMounted(load)
useSeoMeta({ title: 'Settings — CMS Admin' })
</script>

<template>
  <div>
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-black">{{ $t('nav.settings') }}</h1>
      <v-btn color="primary" @click="openCreate">
        <Icon name="solar:add-circle-bold-duotone" size="1.05rem" class="mr-1.5" />
        {{ $t('settingsAdmin.newSetting') }}
      </v-btn>
    </div>

    <v-text-field
      v-model="search"
      :placeholder="$t('settingsAdmin.searchPlaceholder')"
      hide-details
      density="compact"
      style="max-width: 18rem"
      class="mt-6"
    >
      <template #prepend-inner><Icon name="solar:magnifer-bold-duotone" size="1.05rem" /></template>
    </v-text-field>

    <p v-if="loading" class="mt-4 text-sm" style="color: var(--text-faint)">{{ $t('common.loading') }}</p>
    <p v-else-if="!settings.length" class="mt-4 text-sm" style="color: var(--text-faint)">
      {{ search ? $t('settingsAdmin.noSettingsMatch') : $t('settingsAdmin.noSettingsYet') }}
    </p>
    <template v-else>
      <div v-for="(items, category) in grouped" :key="category" class="mt-6">
        <h2 class="text-xs font-bold uppercase" style="color: var(--text-faint)">{{ category }}</h2>
        <div class="bento-card mt-2">
          <div v-for="setting in items" :key="setting.id" class="bento-row">
            <span class="bento-row__icon">
              <Icon :name="setting.is_secret ? 'solar:lock-password-bold-duotone' : 'solar:settings-bold-duotone'" />
            </span>
            <div class="bento-row__body">
              <div class="font-semibold">
                {{ setting.key }}
                <span v-if="setting.is_secret" class="ml-2 text-xs" style="color: var(--text-faint)">
                  {{ setting.has_value ? $t('settingsAdmin.configured') : $t('settingsAdmin.notSet') }}
                </span>
              </div>
              <div class="text-xs" style="color: var(--text-faint)">
                {{ setting.description || (setting.is_secret ? $t('settingsAdmin.secretValue') : JSON.stringify(setting.value)) }}
              </div>
            </div>
            <div class="bento-row__actions">
              <button class="bento-icon-btn bento-icon-btn--primary" :title="$t('common.edit')" @click="openEdit(setting)">
                <Icon name="solar:pen-2-bold-duotone" />
              </button>
              <button class="bento-icon-btn bento-icon-btn--danger" :title="$t('common.delete')" @click="remove(setting)">
                <Icon name="solar:trash-bin-2-bold-duotone" />
              </button>
            </div>
          </div>
        </div>
      </div>
      <div v-if="settings.length" ref="sentinel" class="flex justify-center py-4">
        <span v-if="loadingMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.loadingMore') }}</span>
        <span v-else-if="!hasMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.endOfList') }}</span>
      </div>
    </template>

    <v-dialog v-model="dialog" max-width="480">
      <v-card :title="editing ? $t('settingsAdmin.editSetting') : $t('settingsAdmin.newSetting')">
        <v-card-text class="flex flex-col gap-3">
          <v-text-field v-model="form.key" :label="$t('settingsAdmin.key')" hide-details density="compact" :disabled="!!editing" />
          <v-text-field v-model="form.category" :label="$t('settingsAdmin.category')" hide-details density="compact" />
          <v-text-field v-model="form.description" :label="$t('common.description')" hide-details density="compact" />
          <v-switch v-model="form.is_secret" :label="$t('settingsAdmin.secretLabel')" hide-details density="compact" />
          <v-text-field
            v-model="form.valueText"
            :label="form.is_secret ? $t('settingsAdmin.newValueHint') : $t('settingsAdmin.value')"
            :type="form.is_secret ? 'password' : 'text'"
            hide-details
            density="compact"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="primary" variant="elevated" @click="save">{{ $t('common.save') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
