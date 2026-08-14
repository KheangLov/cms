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

const { t } = useI18n()
const verbFilter = ref('')

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

const { items: logs, loading, loadingMore, hasMore, load, loadMore } = useInfiniteList<LogRow>(() => {
  const query = new URLSearchParams({ ordering: '-timestamp' })
  if (verbFilter.value) query.set('verb', verbFilter.value)
  return `/api/v1/activity-log/?${query}`
})
const sentinel = useInfiniteScrollSentinel(loadMore)

watch(verbFilter, load)
onMounted(load)

useSeoMeta({ title: 'Activity Log — CMS Admin' })
</script>

<template>
  <div>
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-black">{{ $t('activity.title') }}</h1>
      <v-select
        v-model="verbFilter"
        :items="[
          { title: t('activity.allActions'), value: '' },
          { title: t('activity.filterLabels.login'), value: 'login' },
          { title: t('activity.filterLabels.create'), value: 'create' },
          { title: t('activity.filterLabels.update'), value: 'update' },
          { title: t('activity.filterLabels.publish'), value: 'publish' },
          { title: t('activity.filterLabels.unpublish'), value: 'unpublish' },
          { title: t('activity.filterLabels.soft_delete'), value: 'soft_delete' },
          { title: t('activity.filterLabels.restore'), value: 'restore' },
        ]"
        hide-details
        density="compact"
        style="max-width: 12rem"
      />
    </div>

    <p v-if="loading" class="mt-6 text-sm" style="color: var(--text-faint)">{{ $t('common.loading') }}</p>
    <div v-else class="bento-card mt-6">
      <p v-if="!logs.length" class="px-4 py-6 text-sm" style="color: var(--text-faint)">{{ $t('activity.noActivityRecorded') }}</p>
      <div v-for="log in logs" :key="log.id" class="bento-row">
        <span class="bento-row__icon"><Icon :name="iconForVerb(log.verb)" /></span>
        <div class="bento-row__body text-sm">
          <strong>{{ log.actor_email || $t('dashboard.systemActor') }}</strong>
          {{ $t(`activity.verbs.${log.verb}`) }}
          <span style="color: var(--text-secondary)">{{ log.target_repr }}</span>
          <span class="text-xs" style="color: var(--text-faint)">({{ log.target_type }})</span>
          <div class="text-xs" style="color: var(--text-faint)">{{ log.ip_address || '—' }}</div>
        </div>
        <span class="bento-row__actions text-xs" style="color: var(--text-faint)">
          {{ new Date(log.timestamp).toLocaleString() }}
        </span>
      </div>
      <div v-if="logs.length" ref="sentinel" class="flex justify-center py-4">
        <span v-if="loadingMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.loadingMore') }}</span>
        <span v-else-if="!hasMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.endOfList') }}</span>
      </div>
    </div>
  </div>
</template>
