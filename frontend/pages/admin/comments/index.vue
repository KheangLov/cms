<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

interface CommentRow {
  id: number
  resolved_target_type: string
  object_id: number
  author_email: string | null
  body: string
  status: string
  created_at: string
}

const comments = ref<CommentRow[]>([])
const loading = ref(true)
const filter = ref<'pending' | 'approved' | 'spam' | 'all'>('pending')

async function load() {
  loading.value = true
  const path = filter.value === 'all' ? '/api/v1/comments/' : `/api/v1/comments/?status=${filter.value}`
  const resp = await useAuthFetch<{ results: CommentRow[] } | CommentRow[]>(path)
  comments.value = Array.isArray(resp) ? resp : resp.results
  loading.value = false
}

async function approve(comment: CommentRow) {
  await useAuthFetch(`/api/v1/comments/${comment.id}/approve/`, { method: 'POST' })
  await load()
}

async function reject(comment: CommentRow) {
  await useAuthFetch(`/api/v1/comments/${comment.id}/reject/`, { method: 'POST' })
  await load()
}

async function remove(comment: CommentRow) {
  if (!confirm('Delete this comment?')) return
  await useAuthFetch(`/api/v1/comments/${comment.id}/`, { method: 'DELETE' })
  await load()
}

watch(filter, load)
onMounted(load)

useSeoMeta({ title: 'Comments — CMS Admin' })
</script>

<template>
  <div>
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-black">Comments</h1>
      <div class="flex gap-1 rounded-full p-1" style="background: var(--surface-2)">
        <button
          v-for="opt in ['pending', 'approved', 'spam', 'all']"
          :key="opt"
          class="rounded-full px-3 py-1 text-xs font-semibold capitalize"
          :style="filter === opt ? 'background: var(--gradient-primary); color: white' : 'color: var(--text-secondary)'"
          @click="filter = opt as any"
        >
          {{ opt }}
        </button>
      </div>
    </div>

    <p v-if="loading" class="mt-6 text-sm" style="color: var(--text-faint)">Loading…</p>
    <p v-else-if="!comments.length" class="mt-6 text-sm" style="color: var(--text-faint)">Nothing here.</p>
    <ul v-else class="mt-6 divide-y rounded-lg border" style="border-color: var(--border); background: var(--surface)">
      <li v-for="comment in comments" :key="comment.id" class="px-4 py-3">
        <div class="flex items-center justify-between text-xs" style="color: var(--text-faint)">
          <span>
            <strong style="color: var(--text-secondary)">{{ comment.author_email || 'Unknown' }}</strong>
            on {{ comment.resolved_target_type }} #{{ comment.object_id }}
          </span>
          <span>{{ new Date(comment.created_at).toLocaleString() }}</span>
        </div>
        <p class="mt-1 text-sm">{{ comment.body }}</p>
        <div class="mt-2 flex gap-3">
          <button v-if="comment.status !== 'approved'" class="text-xs font-semibold" style="color: var(--success)" @click="approve(comment)">
            Approve
          </button>
          <button v-if="comment.status !== 'spam'" class="text-xs font-semibold" style="color: var(--gold, var(--ember-text))" @click="reject(comment)">
            Mark spam
          </button>
          <button class="text-xs" style="color: var(--error)" @click="remove(comment)">Delete</button>
        </div>
      </li>
    </ul>
  </div>
</template>
