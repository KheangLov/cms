<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

const auth = useAuthStore()
const { t } = useI18n()

interface Stat {
  label: string
  to: string
  count: number | null
  icon: string
  tone: 'ember' | 'wine' | 'gold' | 'info'
}

const stats = computed<Stat[]>(() => [
  { label: t('dashboard.pages'), to: '/admin/pages', count: statCounts.value[0], icon: 'solar:document-2-bold-duotone', tone: 'ember' },
  { label: t('dashboard.posts'), to: '/admin/posts', count: statCounts.value[1], icon: 'solar:notes-bold-duotone', tone: 'wine' },
  { label: t('dashboard.mediaItems'), to: '/admin/media', count: statCounts.value[2], icon: 'solar:gallery-bold-duotone', tone: 'gold' },
  { label: t('dashboard.commentsAwaitingReview'), to: '/admin/comments', count: statCounts.value[3], icon: 'solar:chat-round-dots-bold-duotone', tone: 'info' },
])
const statCounts = ref<(number | null)[]>([null, null, null, null])

const quickActions = computed(() => [
  { to: '/admin/pages', label: t('dashboard.newPage'), icon: 'solar:document-add-bold-duotone' },
  { to: '/admin/posts', label: t('dashboard.newPost'), icon: 'solar:notebook-bold-duotone' },
  { to: '/admin/media', label: t('dashboard.uploadMedia'), icon: 'solar:cloud-upload-bold-duotone' },
])

const verbIcon: Record<string, string> = {
  create: 'solar:add-circle-bold-duotone',
  update: 'solar:pen-2-bold-duotone',
  delete: 'solar:trash-bin-2-bold-duotone',
  soft_delete: 'solar:trash-bin-2-bold-duotone',
  restore: 'solar:undo-left-bold-duotone',
  publish: 'solar:global-bold-duotone',
  unpublish: 'solar:eye-closed-bold-duotone',
  login: 'solar:login-2-bold-duotone',
  logout: 'solar:logout-2-bold-duotone',
}

function iconForVerb(verb: string): string {
  return verbIcon[verb] || 'solar:history-2-bold-duotone'
}

const today = new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })

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
  statCounts.value = [pages, posts, media, comments]
  recentActivity.value = (Array.isArray(activity) ? activity : activity.results).slice(0, 8)
  loading.value = false
})

useSeoMeta({ title: 'Dashboard — CMS Admin' })
</script>

<template>
  <div>
    <h1 class="text-2xl font-black">Dashboard</h1>
    <p class="mt-1 text-sm" style="color: var(--text-secondary)">
      {{ $t('dashboard.welcomeBack') }}{{ auth.user?.email ? ',' : '' }} {{ auth.user?.email }}.
    </p>

    <div class="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
      <div class="bento-tile sm:col-span-2" style="background: var(--gradient-primary); border: none; color: #fff">
        <span class="bento-tile__icon" style="background: rgba(255,255,255,0.22); color: #fff">
          <Icon name="solar:sun-2-bold-duotone" />
        </span>
        <div>
          <div class="text-lg font-black">{{ $t('dashboard.welcomeBack') }}{{ auth.user?.email ? ',' : '' }}</div>
          <div class="text-sm opacity-90">{{ auth.user?.email }}</div>
        </div>
        <div class="mt-auto flex items-center gap-1.5 text-xs font-semibold opacity-90">
          <Icon name="solar:calendar-bold-duotone" />
          {{ today }}
        </div>
      </div>

      <NuxtLink v-for="stat in stats.slice(0, 2)" :key="stat.to" :to="stat.to" class="bento-tile">
        <span class="bento-tile__icon" :class="`bento-tile__icon--${stat.tone}`">
          <Icon :name="stat.icon" />
        </span>
        <div class="text-2xl font-black tabular-nums">
          <v-progress-circular v-if="loading" size="20" width="2" indeterminate color="primary" />
          <template v-else>{{ stat.count }}</template>
        </div>
        <div class="text-xs font-semibold" style="color: var(--text-faint)">{{ stat.label }}</div>
      </NuxtLink>

      <NuxtLink v-for="stat in stats.slice(2)" :key="stat.to" :to="stat.to" class="bento-tile">
        <span class="bento-tile__icon" :class="`bento-tile__icon--${stat.tone}`">
          <Icon :name="stat.icon" />
        </span>
        <div class="text-2xl font-black tabular-nums">
          <v-progress-circular v-if="loading" size="20" width="2" indeterminate color="primary" />
          <template v-else>{{ stat.count }}</template>
        </div>
        <div class="text-xs font-semibold" style="color: var(--text-faint)">{{ stat.label }}</div>
      </NuxtLink>

      <div class="bento-tile sm:col-span-2">
        <div class="text-xs font-bold uppercase" style="color: var(--text-faint)">{{ $t('dashboard.quickActions') }}</div>
        <div class="mt-1 flex flex-wrap gap-2">
          <NuxtLink v-for="action in quickActions" :key="action.to" :to="action.to" class="bento-chip">
            <Icon :name="action.icon" size="1rem" />
            {{ action.label }}
          </NuxtLink>
        </div>
      </div>
    </div>

    <h2 class="mt-8 text-sm font-bold uppercase" style="color: var(--text-faint)">{{ $t('dashboard.recentActivity') }}</h2>
    <div class="bento-card mt-3">
      <p v-if="!loading && !recentActivity.length" class="px-4 py-6 text-sm" style="color: var(--text-faint)">
        {{ $t('dashboard.nothingLoggedYet') }}
      </p>
      <div v-for="row in recentActivity" :key="row.id" class="bento-row">
        <span class="bento-row__icon"><Icon :name="iconForVerb(row.verb)" /></span>
        <span class="bento-row__body text-sm">
          <strong>{{ row.actor_email || $t('dashboard.systemActor') }}</strong>
          {{ $t(`activity.verbs.${row.verb}`) }}
          <span style="color: var(--text-secondary)">{{ row.target_repr }}</span>
        </span>
        <span class="bento-row__actions text-xs" style="color: var(--text-faint)">
          {{ new Date(row.timestamp).toLocaleString() }}
        </span>
      </div>
    </div>
  </div>
</template>
