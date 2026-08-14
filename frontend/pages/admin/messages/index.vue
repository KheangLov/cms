<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

interface MessageRow {
  id: number
  name: string
  email: string
  message: string
  read: boolean
  created_at: string
}

const search = ref('')

const { items: messages, loading, loadingMore, hasMore, load, loadMore } = useInfiniteList<MessageRow>(() => {
  const params = new URLSearchParams()
  if (search.value) params.set('search', search.value)
  return `/api/v1/contact-submissions/?${params}`
})
const sentinel = useInfiniteScrollSentinel(loadMore)

watch(search, useDebounceFn(load, 300))
onMounted(load)

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString()
}

useSeoMeta({ title: 'Messages — CMS Admin' })
</script>

<template>
  <div>
    <h1 class="text-2xl font-black">{{ $t('nav.messages') }}</h1>
    <p class="mt-1 text-sm" style="color: var(--text-faint)">
      {{ $t('messagesAdmin.subtitle') }}
    </p>

    <div class="mt-6 flex flex-wrap items-center gap-3">
      <v-text-field
        v-model="search"
        :placeholder="$t('messagesAdmin.searchPlaceholder')"
        hide-details
        density="compact"
        style="max-width: 18rem"
      >
        <template #prepend-inner><Icon name="solar:magnifer-bold-duotone" size="1.05rem" /></template>
      </v-text-field>
    </div>

    <p v-if="loading" class="mt-4 text-sm" style="color: var(--text-faint)">{{ $t('common.loading') }}</p>
    <div v-else class="bento-card mt-4">
      <p v-if="!messages.length" class="px-4 py-6 text-sm" style="color: var(--text-faint)">
        {{ search ? $t('messagesAdmin.noMessagesMatch') : $t('messagesAdmin.noMessagesYet') }}
      </p>
      <div v-for="msg in messages" :key="msg.id" class="bento-row items-start">
        <span class="bento-row__icon"><Icon name="solar:letter-bold-duotone" /></span>
        <div class="bento-row__body">
          <div class="flex flex-wrap items-baseline gap-2">
            <span class="font-semibold">{{ msg.name }}</span>
            <span class="text-xs" style="color: var(--text-faint)">{{ msg.email }}</span>
            <span class="text-xs" style="color: var(--text-faint)">{{ formatDate(msg.created_at) }}</span>
          </div>
          <p class="mt-1 whitespace-pre-line text-sm" style="color: var(--text-secondary)">{{ msg.message }}</p>
        </div>
      </div>
      <div v-if="messages.length" ref="sentinel" class="flex justify-center py-4">
        <span v-if="loadingMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.loadingMore') }}</span>
        <span v-else-if="!hasMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.endOfList') }}</span>
      </div>
    </div>
  </div>
</template>
