<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

interface RoleRow {
  id: number
  name: string
}

interface UserRow {
  id: number
  email: string
  first_name: string
  last_name: string
  is_active: boolean
  is_staff: boolean
  is_superuser: boolean
  is_2fa_enabled: boolean
  groups: number[]
  groups_detail: RoleRow[]
}

const users = ref<UserRow[]>([])
const roles = ref<RoleRow[]>([])
const loading = ref(true)
const dialog = ref(false)
const editing = ref<UserRow | null>(null)
const form = reactive({
  email: '',
  first_name: '',
  last_name: '',
  is_active: true,
  is_staff: false,
  groups: [] as number[],
  password: '',
})

async function load() {
  loading.value = true
  const [usersResp, rolesResp] = await Promise.all([
    useAuthFetch<{ results: UserRow[] } | UserRow[]>('/api/v1/users/'),
    useAuthFetch<{ results: RoleRow[] } | RoleRow[]>('/api/v1/roles/'),
  ])
  users.value = Array.isArray(usersResp) ? usersResp : usersResp.results
  roles.value = Array.isArray(rolesResp) ? rolesResp : rolesResp.results
  loading.value = false
}

function openCreate() {
  editing.value = null
  Object.assign(form, { email: '', first_name: '', last_name: '', is_active: true, is_staff: false, groups: [], password: '' })
  dialog.value = true
}

function openEdit(user: UserRow) {
  editing.value = user
  Object.assign(form, {
    email: user.email,
    first_name: user.first_name,
    last_name: user.last_name,
    is_active: user.is_active,
    is_staff: user.is_staff,
    groups: [...user.groups],
    password: '',
  })
  dialog.value = true
}

async function save() {
  const body: Record<string, unknown> = {
    email: form.email,
    first_name: form.first_name,
    last_name: form.last_name,
    is_active: form.is_active,
    is_staff: form.is_staff,
    groups: form.groups,
  }
  if (form.password) body.password = form.password
  if (editing.value) {
    await useAuthFetch(`/api/v1/users/${editing.value.id}/`, { method: 'PATCH', body })
  } else {
    await useAuthFetch('/api/v1/users/', { method: 'POST', body })
  }
  dialog.value = false
  await load()
}

async function deactivate(user: UserRow) {
  if (!confirm(`Deactivate "${user.email}"? They will no longer be able to log in.`)) return
  await useAuthFetch(`/api/v1/users/${user.id}/`, { method: 'DELETE' })
  await load()
}

onMounted(load)
useSeoMeta({ title: 'Users — CMS Admin' })
</script>

<template>
  <div>
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-black">Users</h1>
      <v-btn color="primary" @click="openCreate">New user</v-btn>
    </div>

    <p v-if="loading" class="mt-6 text-sm" style="color: var(--text-faint)">Loading…</p>
    <ul v-else class="mt-6 divide-y rounded-lg border" style="border-color: var(--border); background: var(--surface)">
      <li v-for="user in users" :key="user.id" class="flex items-center justify-between px-4 py-3">
        <div>
          <div class="font-semibold">
            {{ user.email }}
            <span v-if="user.is_superuser" class="ml-2 text-xs" style="color: var(--gold, var(--ember-text))">superuser</span>
            <span v-if="!user.is_active" class="ml-2 text-xs" style="color: var(--error)">inactive</span>
          </div>
          <div class="text-xs" style="color: var(--text-faint)">
            {{ [user.first_name, user.last_name].filter(Boolean).join(' ') || '—' }}
            <template v-if="user.groups_detail.length"> · {{ user.groups_detail.map((g) => g.name).join(', ') }}</template>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <button class="text-xs font-semibold" style="color: var(--info)" @click="openEdit(user)">Edit</button>
          <button v-if="user.is_active" class="text-xs" style="color: var(--error)" @click="deactivate(user)">
            Deactivate
          </button>
        </div>
      </li>
    </ul>

    <v-dialog v-model="dialog" max-width="480">
      <v-card :title="editing ? 'Edit user' : 'New user'">
        <v-card-text class="flex flex-col gap-3">
          <v-text-field v-model="form.email" label="Email" hide-details density="compact" :disabled="!!editing" />
          <div class="flex gap-3">
            <v-text-field v-model="form.first_name" label="First name" hide-details density="compact" />
            <v-text-field v-model="form.last_name" label="Last name" hide-details density="compact" />
          </div>
          <v-select
            v-model="form.groups"
            :items="roles"
            item-title="name"
            item-value="id"
            label="Roles"
            multiple
            chips
            hide-details
            density="compact"
          />
          <v-text-field
            v-model="form.password"
            :label="editing ? 'New password (leave blank to keep current)' : 'Password'"
            type="password"
            hide-details
            density="compact"
          />
          <div class="flex gap-6">
            <v-switch v-model="form.is_active" label="Active" hide-details density="compact" />
            <v-switch v-model="form.is_staff" label="Staff (can access admin)" hide-details density="compact" />
          </div>
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
