<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

interface PostRow {
  id: number
  slug: string
  status: string
  published_at: string | null
  translations: Array<{ locale: string; title: string }>
}

const posts = ref<PostRow[]>([])
const loading = ref(true)
const creating = ref(false)
const newSlug = ref('')
const router = useRouter()

async function load() {
  loading.value = true
  const resp = await useAuthFetch<{ results: PostRow[] } | PostRow[]>('/api/v1/posts/?trash=0')
  posts.value = Array.isArray(resp) ? resp : resp.results
  loading.value = false
}

function titleFor(post: PostRow): string {
  return post.translations.find((t) => t.locale === 'en')?.title || post.slug
}

async function createPost() {
  if (!newSlug.value) return
  const created = await useAuthFetch<PostRow>('/api/v1/posts/', {
    method: 'POST',
    body: { slug: newSlug.value, translations: [{ locale: 'en', title: newSlug.value }] },
  })
  creating.value = false
  newSlug.value = ''
  await router.push(`/admin/posts/${created.id}`)
}

async function togglePublish(post: PostRow) {
  const action = post.status === 'published' ? 'unpublish' : 'publish'
  await useAuthFetch(`/api/v1/posts/${post.id}/${action}/`, { method: 'POST' })
  await load()
}

async function removePost(post: PostRow) {
  if (!confirm(`Delete "${titleFor(post)}"? This can be restored later from the trash.`)) return
  await useAuthFetch(`/api/v1/posts/${post.id}/`, { method: 'DELETE' })
  posts.value = posts.value.filter((p) => p.id !== post.id)
}

onMounted(load)

useSeoMeta({ title: 'Posts — CMS Admin' })
</script>

<template>
  <div>
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-black">Posts</h1>
      <div class="flex items-center gap-4">
        <NuxtLink to="/admin/categories" class="text-sm font-semibold" style="color: var(--text-secondary)">
          Categories
        </NuxtLink>
        <NuxtLink to="/admin/tags" class="text-sm font-semibold" style="color: var(--text-secondary)">Tags</NuxtLink>
        <v-btn color="primary" @click="creating = true">New post</v-btn>
      </div>
    </div>

    <div v-if="creating" class="mt-4 flex flex-wrap items-end gap-3 rounded-lg border p-4" style="border-color: var(--border); background: var(--surface)">
      <v-text-field v-model="newSlug" label="Slug" hide-details density="compact" style="max-width: 16rem" />
      <v-btn color="primary" @click="createPost">Create</v-btn>
      <v-btn variant="text" @click="creating = false">Cancel</v-btn>
    </div>

    <p v-if="loading" class="mt-6 text-sm" style="color: var(--text-faint)">Loading…</p>
    <ul v-else class="mt-6 divide-y rounded-lg border" style="border-color: var(--border); background: var(--surface)">
      <li v-if="!posts.length" class="px-4 py-6 text-sm" style="color: var(--text-faint)">No posts yet.</li>
      <li v-for="post in posts" :key="post.id" class="flex items-center justify-between px-4 py-3">
        <div>
          <div class="font-semibold">{{ titleFor(post) }}</div>
          <div class="text-xs" style="color: var(--text-faint)">/{{ post.slug }} — {{ post.status }}</div>
        </div>
        <div class="flex items-center gap-3">
          <button class="text-xs font-semibold" style="color: var(--info)" @click="togglePublish(post)">
            {{ post.status === 'published' ? 'Unpublish' : 'Publish' }}
          </button>
          <NuxtLink :to="`/admin/posts/${post.id}`" class="text-sm font-bold text-primary"> Edit blocks → </NuxtLink>
          <button class="text-xs" style="color: var(--error)" @click="removePost(post)">Delete</button>
        </div>
      </li>
    </ul>
  </div>
</template>
