<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

interface LogRow {
  id: number
  actor_email: string | null
  verb: string
  target_type: string
  target_repr: string
  ip_address: string | null
  timestamp: string
}

const logs = ref<LogRow[]>([])
const loading = ref(true)
const verbFilter = ref('')

async function load() {
  loading.value = true
  const query = new URLSearchParams({ ordering: '-timestamp' })
  if (verbFilter.value) query.set('verb', verbFilter.value)
  const resp = await useAuthFetch<{ results: LogRow[] } | LogRow[]>(`/api/v1/activity-log/?${query}`)
  logs.value = Array.isArray(resp) ? resp : resp.results
  loading.value = false
}

watch(verbFilter, load)
onMounted(load)

useSeoMeta({ title: 'Activity Log — CMS Admin' })
</script>

<template>
  <div>
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-black">Activity Log</h1>
      <v-select
        v-model="verbFilter"
        :items="[
          { title: 'All actions', value: '' },
          { title: 'Login', value: 'login' },
          { title: 'Create', value: 'create' },
          { title: 'Update', value: 'update' },
          { title: 'Publish', value: 'publish' },
          { title: 'Unpublish', value: 'unpublish' },
          { title: 'Soft delete', value: 'soft_delete' },
          { title: 'Restore', value: 'restore' },
        ]"
        hide-details
        density="compact"
        style="max-width: 12rem"
      />
    </div>

    <p v-if="loading" class="mt-6 text-sm" style="color: var(--text-faint)">Loading…</p>
    <div v-else class="mt-6 overflow-x-auto rounded-lg border" style="border-color: var(--border); background: var(--surface)">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b text-left text-xs uppercase" style="border-color: var(--border); color: var(--text-faint)">
            <th class="px-4 py-2">Actor</th>
            <th class="px-4 py-2">Action</th>
            <th class="px-4 py-2">Target</th>
            <th class="px-4 py-2">IP</th>
            <th class="px-4 py-2">When</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!logs.length">
            <td colspan="5" class="px-4 py-6 text-center" style="color: var(--text-faint)">No activity recorded.</td>
          </tr>
          <tr v-for="log in logs" :key="log.id" class="border-b last:border-0" style="border-color: var(--border)">
            <td class="px-4 py-2">{{ log.actor_email || 'System' }}</td>
            <td class="px-4 py-2">{{ log.verb }}</td>
            <td class="px-4 py-2" style="color: var(--text-secondary)">{{ log.target_repr }} ({{ log.target_type }})</td>
            <td class="px-4 py-2" style="color: var(--text-faint)">{{ log.ip_address || '—' }}</td>
            <td class="px-4 py-2" style="color: var(--text-faint)">{{ new Date(log.timestamp).toLocaleString() }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
