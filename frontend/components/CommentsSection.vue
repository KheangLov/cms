<script setup lang="ts">
interface CommentNode {
  id: number
  author_name: string
  body: string
  created_at: string
  replies: CommentNode[]
}

defineProps<{ comments: CommentNode[] }>()

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })
}
</script>

<template>
  <section v-if="comments.length" class="mt-12 border-t pt-8" style="border-color: var(--border)">
    <h2 class="text-xl font-black">{{ $t('comments.count', { n: comments.length }) }}</h2>
    <ul class="mt-6 space-y-6">
      <li v-for="comment in comments" :key="comment.id">
        <div class="flex items-start gap-3">
          <span
            class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-sm font-bold"
            style="background: var(--tonal-bg); color: var(--ember-text)"
          >
            {{ comment.author_name.charAt(0).toUpperCase() }}
          </span>
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-baseline gap-2">
              <span class="font-semibold">{{ comment.author_name }}</span>
              <span class="text-xs" style="color: var(--text-faint)">{{ formatDate(comment.created_at) }}</span>
            </div>
            <p class="mt-1 whitespace-pre-line text-sm" style="color: var(--text-secondary)">{{ comment.body }}</p>
          </div>
        </div>
        <ul v-if="comment.replies.length" class="mt-4 ml-12 space-y-4 border-l pl-4" style="border-color: var(--border)">
          <li v-for="reply in comment.replies" :key="reply.id">
            <div class="flex items-start gap-3">
              <span
                class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold"
                style="background: var(--surface-2); color: var(--text-secondary)"
              >
                {{ reply.author_name.charAt(0).toUpperCase() }}
              </span>
              <div class="min-w-0 flex-1">
                <div class="flex flex-wrap items-baseline gap-2">
                  <span class="text-sm font-semibold">{{ reply.author_name }}</span>
                  <span class="text-xs" style="color: var(--text-faint)">{{ formatDate(reply.created_at) }}</span>
                </div>
                <p class="mt-1 whitespace-pre-line text-sm" style="color: var(--text-secondary)">{{ reply.body }}</p>
              </div>
            </div>
          </li>
        </ul>
      </li>
    </ul>
  </section>
</template>
