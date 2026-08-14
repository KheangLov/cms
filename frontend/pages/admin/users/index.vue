<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

const { confirm } = useConfirmDialog()
const { t } = useI18n()

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

const roles = ref<RoleRow[]>([])
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

const search = ref('')
const activeFilter = ref<string | null>(null)

const { items: users, loading, loadingMore, hasMore, load, loadMore } = useInfiniteList<UserRow>(() => {
  const params = new URLSearchParams()
  if (search.value) params.set('search', search.value)
  if (activeFilter.value !== null) params.set('is_active', activeFilter.value)
  return `/api/v1/users/?${params}`
})
const sentinel = useInfiniteScrollSentinel(loadMore)

// Roles are a fixed, small dropdown source for the edit form — not part of the
// infinite-scrolled resource, so they get their own plain one-shot fetch.
async function loadRoles() {
  const resp = await useAuthFetch<{ results: RoleRow[] } | RoleRow[]>('/api/v1/roles/')
  roles.value = Array.isArray(resp) ? resp : resp.results
}

const debouncedLoad = useDebounceFn(load, 300)
watch(search, debouncedLoad)
watch(activeFilter, load)

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
  const ok = await confirm({
    title: t('usersAdmin.deactivateTitle'),
    message: t('usersAdmin.deactivateMessage', { email: user.email }),
    confirmLabel: t('usersAdmin.deactivate'),
  })
  if (!ok) return
  await useAuthFetch(`/api/v1/users/${user.id}/`, { method: 'DELETE' })
  await load()
}

onMounted(() => {
  load()
  loadRoles()
})
useSeoMeta({ title: 'Users — CMS Admin' })
</script>

<template>
  <div>
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-black">{{ $t('nav.users') }}</h1>
      <v-btn color="primary" @click="openCreate">
        <Icon name="solar:add-circle-bold-duotone" size="1.05rem" class="mr-1.5" />
        {{ $t('usersAdmin.newUser') }}
      </v-btn>
    </div>

    <div class="mt-6 flex flex-wrap items-center gap-3">
      <v-text-field
        v-model="search"
        :placeholder="$t('usersAdmin.searchPlaceholder')"
        hide-details
        density="compact"
        style="max-width: 18rem"
      >
        <template #prepend-inner><Icon name="solar:magnifer-bold-duotone" size="1.05rem" /></template>
      </v-text-field>
      <v-select
        v-model="activeFilter"
        :items="[
          { title: $t('usersAdmin.allUsers'), value: null },
          { title: $t('usersAdmin.active'), value: 'true' },
          { title: $t('usersAdmin.inactive'), value: 'false' },
        ]"
        hide-details
        density="compact"
        style="max-width: 12rem"
      />
    </div>

    <p v-if="loading" class="mt-4 text-sm" style="color: var(--text-faint)">{{ $t('common.loading') }}</p>
    <div v-else class="bento-card mt-4">
      <p v-if="!users.length" class="px-4 py-6 text-sm" style="color: var(--text-faint)">{{ $t('usersAdmin.noUsersMatch') }}</p>
      <div v-for="user in users" :key="user.id" class="bento-row">
        <span class="bento-row__icon"><Icon name="solar:user-circle-bold-duotone" /></span>
        <div class="bento-row__body">
          <div class="font-semibold">
            {{ user.email }}
            <span v-if="user.is_superuser" class="ml-2 text-xs" style="color: var(--gold-text)">{{ $t('usersAdmin.superuser') }}</span>
            <span v-if="!user.is_active" class="ml-2 text-xs" style="color: var(--error)">{{ $t('usersAdmin.inactive') }}</span>
          </div>
          <div class="text-xs" style="color: var(--text-faint)">
            {{ [user.first_name, user.last_name].filter(Boolean).join(' ') || '—' }}
            <template v-if="user.groups_detail.length"> · {{ user.groups_detail.map((g) => g.name).join(', ') }}</template>
          </div>
        </div>
        <div class="bento-row__actions">
          <button class="bento-icon-btn bento-icon-btn--primary" :title="$t('common.edit')" @click="openEdit(user)">
            <Icon name="solar:pen-2-bold-duotone" />
          </button>
          <button v-if="user.is_active" class="bento-icon-btn bento-icon-btn--danger" :title="$t('usersAdmin.deactivate')" @click="deactivate(user)">
            <Icon name="solar:user-block-bold-duotone" />
          </button>
        </div>
      </div>
      <div v-if="users.length" ref="sentinel" class="flex justify-center py-4">
        <span v-if="loadingMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.loadingMore') }}</span>
        <span v-else-if="!hasMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.endOfList') }}</span>
      </div>
    </div>

    <v-dialog v-model="dialog" max-width="480">
      <v-card :title="editing ? $t('usersAdmin.editUser') : $t('usersAdmin.newUser')">
        <v-card-text class="flex flex-col gap-3">
          <v-text-field v-model="form.email" :label="$t('common.email')" hide-details density="compact" :disabled="!!editing" />
          <div class="flex gap-3">
            <v-text-field v-model="form.first_name" :label="$t('account.firstName')" hide-details density="compact" />
            <v-text-field v-model="form.last_name" :label="$t('account.lastName')" hide-details density="compact" />
          </div>
          <v-select
            v-model="form.groups"
            :items="roles"
            item-title="name"
            item-value="id"
            :label="$t('usersAdmin.roles')"
            multiple
            chips
            hide-details
            density="compact"
          />
          <v-text-field
            v-model="form.password"
            :label="editing ? $t('usersAdmin.newPasswordHint') : $t('usersAdmin.password')"
            type="password"
            hide-details
            density="compact"
          />
          <div class="flex gap-6">
            <v-switch v-model="form.is_active" :label="$t('usersAdmin.active')" hide-details density="compact" />
            <v-switch v-model="form.is_staff" :label="$t('usersAdmin.staffHint')" hide-details density="compact" />
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
