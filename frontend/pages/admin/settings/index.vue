<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

interface SettingRow {
  id: number
  key: string
  value: unknown
  category: string
  is_secret: boolean
  description: string
  has_value?: boolean
}

const settings = ref<SettingRow[]>([])
const loading = ref(true)
const dialog = ref(false)
const editing = ref<SettingRow | null>(null)
const form = reactive({ key: '', valueText: '', category: 'general', is_secret: false, description: '' })

const grouped = computed(() => {
  const groups: Record<string, SettingRow[]> = {}
  for (const s of settings.value) {
    ;(groups[s.category] ||= []).push(s)
  }
  return groups
})

async function load() {
  loading.value = true
  const resp = await useAuthFetch<{ results: SettingRow[] } | SettingRow[]>('/api/v1/settings/')
  settings.value = Array.isArray(resp) ? resp : resp.results
  loading.value = false
}

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
    await useAuthFetch(`/api/v1/settings/${editing.value.id}/`, { method: 'PATCH', body })
  } else {
    await useAuthFetch('/api/v1/settings/', { method: 'POST', body })
  }
  dialog.value = false
  await load()
}

async function remove(setting: SettingRow) {
  if (!confirm(`Delete setting "${setting.key}"?`)) return
  await useAuthFetch(`/api/v1/settings/${setting.id}/`, { method: 'DELETE' })
  await load()
}

onMounted(load)
useSeoMeta({ title: 'Settings — CMS Admin' })
</script>

<template>
  <div>
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-black">Settings</h1>
      <v-btn color="primary" @click="openCreate">New setting</v-btn>
    </div>

    <p v-if="loading" class="mt-6 text-sm" style="color: var(--text-faint)">Loading…</p>
    <template v-else>
      <div v-for="(items, category) in grouped" :key="category" class="mt-6">
        <h2 class="text-xs font-bold uppercase" style="color: var(--text-faint)">{{ category }}</h2>
        <ul class="mt-2 divide-y rounded-lg border" style="border-color: var(--border); background: var(--surface)">
          <li v-for="setting in items" :key="setting.id" class="flex items-center justify-between px-4 py-3">
            <div>
              <div class="font-semibold">
                {{ setting.key }}
                <span v-if="setting.is_secret" class="ml-2 text-xs" style="color: var(--text-faint)">
                  {{ setting.has_value ? '(configured)' : '(not set)' }}
                </span>
              </div>
              <div class="text-xs" style="color: var(--text-faint)">
                {{ setting.description || (setting.is_secret ? 'Secret value' : JSON.stringify(setting.value)) }}
              </div>
            </div>
            <div class="flex items-center gap-3">
              <button class="text-xs font-semibold" style="color: var(--info)" @click="openEdit(setting)">Edit</button>
              <button class="text-xs" style="color: var(--error)" @click="remove(setting)">Delete</button>
            </div>
          </li>
        </ul>
      </div>
    </template>

    <v-dialog v-model="dialog" max-width="480">
      <v-card :title="editing ? 'Edit setting' : 'New setting'">
        <v-card-text class="flex flex-col gap-3">
          <v-text-field v-model="form.key" label="Key" hide-details density="compact" :disabled="!!editing" />
          <v-text-field v-model="form.category" label="Category" hide-details density="compact" />
          <v-text-field v-model="form.description" label="Description" hide-details density="compact" />
          <v-switch v-model="form.is_secret" label="Secret (encrypted at rest)" hide-details density="compact" />
          <v-text-field
            v-model="form.valueText"
            :label="form.is_secret ? 'New value (leave blank to keep current)' : 'Value'"
            :type="form.is_secret ? 'password' : 'text'"
            hide-details
            density="compact"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="save">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
