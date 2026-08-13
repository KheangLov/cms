<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

interface TagRow {
  id: number
  name: string
  slug: string
}

const tags = ref<TagRow[]>([])
const loading = ref(true)
const dialog = ref(false)
const editing = ref<TagRow | null>(null)
const form = reactive({ name: '', slug: '' })

async function load() {
  loading.value = true
  const resp = await useAuthFetch<{ results: TagRow[] } | TagRow[]>('/api/v1/tags/')
  tags.value = Array.isArray(resp) ? resp : resp.results
  loading.value = false
}

function openCreate() {
  editing.value = null
  form.name = ''
  form.slug = ''
  dialog.value = true
}

function openEdit(tag: TagRow) {
  editing.value = tag
  form.name = tag.name
  form.slug = tag.slug
  dialog.value = true
}

async function save() {
  const body = { name: form.name, slug: form.slug, translations: [{ locale: 'en', name: form.name }] }
  if (editing.value) {
    await useAuthFetch(`/api/v1/tags/${editing.value.id}/`, { method: 'PATCH', body })
  } else {
    await useAuthFetch('/api/v1/tags/', { method: 'POST', body })
  }
  dialog.value = false
  await load()
}

async function remove(tag: TagRow) {
  if (!confirm(`Delete tag "${tag.name}"?`)) return
  await useAuthFetch(`/api/v1/tags/${tag.id}/`, { method: 'DELETE' })
  await load()
}

onMounted(load)
useSeoMeta({ title: 'Tags — CMS Admin' })
</script>

<template>
  <div>
    <div class="flex items-center justify-between">
      <div>
        <NuxtLink to="/admin/posts" class="text-sm" style="color: var(--text-faint)">&larr; Posts</NuxtLink>
        <h1 class="text-2xl font-black">Tags</h1>
      </div>
      <v-btn color="primary" @click="openCreate">New tag</v-btn>
    </div>

    <p v-if="loading" class="mt-6 text-sm" style="color: var(--text-faint)">Loading…</p>
    <ul v-else class="mt-6 divide-y rounded-lg border" style="border-color: var(--border); background: var(--surface)">
      <li v-if="!tags.length" class="px-4 py-6 text-sm" style="color: var(--text-faint)">No tags yet.</li>
      <li v-for="tag in tags" :key="tag.id" class="flex items-center justify-between px-4 py-3">
        <div>
          <div class="font-semibold">{{ tag.name }}</div>
          <div class="text-xs" style="color: var(--text-faint)">/{{ tag.slug }}</div>
        </div>
        <div class="flex items-center gap-3">
          <button class="text-xs font-semibold" style="color: var(--info)" @click="openEdit(tag)">Edit</button>
          <button class="text-xs" style="color: var(--error)" @click="remove(tag)">Delete</button>
        </div>
      </li>
    </ul>

    <v-dialog v-model="dialog" max-width="420">
      <v-card :title="editing ? 'Edit tag' : 'New tag'">
        <v-card-text class="flex flex-col gap-3">
          <v-text-field v-model="form.name" label="Name" hide-details density="compact" />
          <v-text-field v-model="form.slug" label="Slug" hide-details density="compact" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="save">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
