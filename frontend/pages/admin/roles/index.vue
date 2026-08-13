<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

interface PermissionRow {
  id: number
  name: string
  codename: string
  app_label: string
}

interface RoleRow {
  id: number
  name: string
  permissions: number[]
}

const roles = ref<RoleRow[]>([])
const permissions = ref<PermissionRow[]>([])
const loading = ref(true)
const dialog = ref(false)
const editing = ref<RoleRow | null>(null)
const form = reactive({ name: '', permissions: [] as number[] })

const groupedPermissions = computed(() => {
  const groups: Record<string, PermissionRow[]> = {}
  for (const p of permissions.value) {
    ;(groups[p.app_label] ||= []).push(p)
  }
  return groups
})

async function load() {
  loading.value = true
  const [rolesResp, permsResp] = await Promise.all([
    useAuthFetch<{ results: RoleRow[] } | RoleRow[]>('/api/v1/roles/'),
    useAuthFetch<{ results: PermissionRow[]; count: number } | PermissionRow[]>('/api/v1/permissions/?page_size=500'),
  ])
  roles.value = Array.isArray(rolesResp) ? rolesResp : rolesResp.results
  permissions.value = Array.isArray(permsResp) ? permsResp : permsResp.results
  loading.value = false
}

function openCreate() {
  editing.value = null
  form.name = ''
  form.permissions = []
  dialog.value = true
}

function openEdit(role: RoleRow) {
  editing.value = role
  form.name = role.name
  form.permissions = [...role.permissions]
  dialog.value = true
}

function togglePerm(id: number) {
  const idx = form.permissions.indexOf(id)
  if (idx === -1) form.permissions.push(id)
  else form.permissions.splice(idx, 1)
}

async function save() {
  const body = { name: form.name, permissions: form.permissions }
  if (editing.value) {
    await useAuthFetch(`/api/v1/roles/${editing.value.id}/`, { method: 'PATCH', body })
  } else {
    await useAuthFetch('/api/v1/roles/', { method: 'POST', body })
  }
  dialog.value = false
  await load()
}

async function remove(role: RoleRow) {
  if (!confirm(`Delete role "${role.name}"?`)) return
  await useAuthFetch(`/api/v1/roles/${role.id}/`, { method: 'DELETE' })
  await load()
}

onMounted(load)
useSeoMeta({ title: 'Roles — CMS Admin' })
</script>

<template>
  <div>
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-black">Roles</h1>
      <v-btn color="primary" @click="openCreate">New role</v-btn>
    </div>

    <p v-if="loading" class="mt-6 text-sm" style="color: var(--text-faint)">Loading…</p>
    <ul v-else class="mt-6 divide-y rounded-lg border" style="border-color: var(--border); background: var(--surface)">
      <li v-for="role in roles" :key="role.id" class="flex items-center justify-between px-4 py-3">
        <div>
          <div class="font-semibold">{{ role.name }}</div>
          <div class="text-xs" style="color: var(--text-faint)">{{ role.permissions.length }} permissions</div>
        </div>
        <div class="flex items-center gap-3">
          <button class="text-xs font-semibold" style="color: var(--info)" @click="openEdit(role)">Edit</button>
          <button class="text-xs" style="color: var(--error)" @click="remove(role)">Delete</button>
        </div>
      </li>
    </ul>

    <v-dialog v-model="dialog" max-width="640">
      <v-card :title="editing ? 'Edit role' : 'New role'">
        <v-card-text class="flex flex-col gap-3">
          <v-text-field v-model="form.name" label="Role name" hide-details density="compact" />
          <div class="max-h-96 overflow-y-auto rounded border p-3" style="border-color: var(--border)">
            <details v-for="(perms, appLabel) in groupedPermissions" :key="appLabel" class="mb-2">
              <summary class="cursor-pointer text-xs font-bold uppercase" style="color: var(--text-faint)">
                {{ appLabel }}
              </summary>
              <label
                v-for="perm in perms"
                :key="perm.id"
                class="mt-1 flex items-center gap-2 pl-3 text-sm"
              >
                <input
                  type="checkbox"
                  :checked="form.permissions.includes(perm.id)"
                  @change="togglePerm(perm.id)"
                />
                {{ perm.name }}
              </label>
            </details>
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
