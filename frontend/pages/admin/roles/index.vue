<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

const { confirm } = useConfirmDialog()
const { t } = useI18n()

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

const permissions = ref<PermissionRow[]>([])
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

const { items: roles, loading, loadingMore, hasMore, load, loadMore } = useInfiniteList<RoleRow>(
  () => '/api/v1/roles/',
)
const sentinel = useInfiniteScrollSentinel(loadMore)

// Every permission is needed up front for the edit dialog's checkbox list —
// not something to infinite-scroll — so this stays a plain one-shot fetch,
// now actually complete since ?page_size= is honored (apps/common/pagination.py).
async function loadPermissions() {
  const resp = await useAuthFetch<{ results: PermissionRow[] } | PermissionRow[]>('/api/v1/permissions/?page_size=200')
  permissions.value = Array.isArray(resp) ? resp : resp.results
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
  if (!(await confirm({ message: t('rolesAdmin.deleteConfirm', { name: role.name }), danger: true }))) return
  await useAuthFetch(`/api/v1/roles/${role.id}/`, { method: 'DELETE' })
  await load()
}

onMounted(() => {
  load()
  loadPermissions()
})
useSeoMeta({ title: 'Roles — CMS Admin' })
</script>

<template>
  <div>
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-black">{{ $t('rolesAdmin.title') }}</h1>
      <v-btn color="primary" @click="openCreate">
        <Icon name="solar:add-circle-bold-duotone" size="1.05rem" class="mr-1.5" />
        {{ $t('rolesAdmin.newRole') }}
      </v-btn>
    </div>

    <p v-if="loading" class="mt-6 text-sm" style="color: var(--text-faint)">{{ $t('common.loading') }}</p>
    <div v-else class="bento-card mt-6">
      <div v-for="role in roles" :key="role.id" class="bento-row">
        <span class="bento-row__icon"><Icon name="solar:shield-user-bold-duotone" /></span>
        <div class="bento-row__body">
          <div class="font-semibold">{{ role.name }}</div>
          <div class="text-xs" style="color: var(--text-faint)">{{ $t('rolesAdmin.permissionsCount', { n: role.permissions.length }) }}</div>
        </div>
        <div class="bento-row__actions">
          <button class="bento-icon-btn bento-icon-btn--primary" :title="$t('common.edit')" @click="openEdit(role)">
            <Icon name="solar:pen-2-bold-duotone" />
          </button>
          <button class="bento-icon-btn bento-icon-btn--danger" :title="$t('common.delete')" @click="remove(role)">
            <Icon name="solar:trash-bin-2-bold-duotone" />
          </button>
        </div>
      </div>
      <div v-if="roles.length" ref="sentinel" class="flex justify-center py-4">
        <span v-if="loadingMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.loadingMore') }}</span>
        <span v-else-if="!hasMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.endOfList') }}</span>
      </div>
    </div>

    <v-dialog v-model="dialog" max-width="640">
      <v-card :title="editing ? $t('rolesAdmin.editRole') : $t('rolesAdmin.newRole')">
        <v-card-text class="flex flex-col gap-3">
          <v-text-field v-model="form.name" :label="$t('rolesAdmin.roleName')" hide-details density="compact" />
          <div
            class="max-h-96 overflow-y-auto p-3"
            style="background: var(--surface-2); border-radius: var(--radius-md)"
          >
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
          <v-btn variant="text" @click="dialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="primary" variant="elevated" @click="save">{{ $t('common.save') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
