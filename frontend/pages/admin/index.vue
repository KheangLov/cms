<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

const auth = useAuthStore()

interface Stat {
  label: string
  to: string
  count: number | null
}

const stats = ref<Stat[]>([
  { label: 'Pages', to: '/admin/pages', count: null },
  { label: 'Posts', to: '/admin/posts', count: null },
  { label: 'Media items', to: '/admin/media', count: null },
  { label: 'Comments awaiting review', to: '/admin/comments', count: null },
])

interface ActivityRow {
  id: number
  actor_email: string | null
  verb: string
  target_repr: string
  timestamp: string
}

const recentActivity = ref<ActivityRow[]>([])
const loading = ref(true)

async function loadCount(path: string): Promise<number> {
  try {
    const resp = await useAuthFetch<{ count: number }>(path)
    return resp.count ?? 0
  } catch {
    return 0
  }
}

onMounted(async () => {
  const [pages, posts, media, comments, activity] = await Promise.all([
    loadCount('/api/v1/pages/?trash=0'),
    loadCount('/api/v1/posts/'),
    loadCount('/api/v1/media/'),
    loadCount('/api/v1/comments/?status=pending'),
    useAuthFetch<{ results: ActivityRow[] } | ActivityRow[]>('/api/v1/activity-log/?ordering=-timestamp').catch(
      () => [],
    ),
  ])
  stats.value[0].count = pages
  stats.value[1].count = posts
  stats.value[2].count = media
  stats.value[3].count = comments
  recentActivity.value = (Array.isArray(activity) ? activity : activity.results).slice(0, 8)
  loading.value = false
})

useSeoMeta({ title: 'Dashboard — CMS Admin' })
</script>

<template>
  <div>
    <h1 class="text-2xl font-black">Dashboard</h1>
    <p class="mt-1 text-sm" style="color: var(--text-secondary)">
      Welcome back{{ auth.user?.email ? ',' : '' }} {{ auth.user?.email }}.
    </p>

    <div class="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
      <NuxtLink
        v-for="stat in stats"
        :key="stat.label"
        :to="stat.to"
        class="rounded-lg border p-4"
        style="border-color: var(--border); background: var(--surface)"
      >
        <div class="text-2xl font-black tabular-nums">
          <v-progress-circular v-if="loading" size="20" width="2" indeterminate color="primary" />
          <template v-else>{{ stat.count }}</template>
        </div>
        <div class="mt-1 text-xs font-semibold" style="color: var(--text-faint)">{{ stat.label }}</div>
      </NuxtLink>
    </div>

    <h2 class="mt-8 text-sm font-bold uppercase" style="color: var(--text-faint)">Recent activity</h2>
    <div class="mt-3 divide-y rounded-lg border" style="border-color: var(--border); background: var(--surface)">
      <p v-if="!loading && !recentActivity.length" class="px-4 py-6 text-sm" style="color: var(--text-faint)">
        Nothing logged yet.
      </p>
      <div
        v-for="row in recentActivity"
        :key="row.id"
        class="flex items-center justify-between px-4 py-3 text-sm"
        style="border-color: var(--border)"
      >
        <span>
          <strong>{{ row.actor_email || 'System' }}</strong>
          {{ row.verb }}
          <span style="color: var(--text-secondary)">{{ row.target_repr }}</span>
        </span>
        <span class="text-xs" style="color: var(--text-faint)">{{ new Date(row.timestamp).toLocaleString() }}</span>
      </div>
    </div>
  </div>
</template>
