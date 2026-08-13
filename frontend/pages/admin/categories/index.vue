<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

interface CategoryRow {
  id: number
  name: string
  slug: string
  parent: number | null
}

const categories = ref<CategoryRow[]>([])
const loading = ref(true)
const dialog = ref(false)
const editing = ref<CategoryRow | null>(null)
const form = reactive({ name: '', slug: '' })

async function load() {
  loading.value = true
  const resp = await useAuthFetch<{ results: CategoryRow[] } | CategoryRow[]>('/api/v1/categories/')
  categories.value = Array.isArray(resp) ? resp : resp.results
  loading.value = false
}

function openCreate() {
  editing.value = null
  form.name = ''
  form.slug = ''
  dialog.value = true
}

function openEdit(cat: CategoryRow) {
  editing.value = cat
  form.name = cat.name
  form.slug = cat.slug
  dialog.value = true
}

async function save() {
  const body = { name: form.name, slug: form.slug, translations: [{ locale: 'en', name: form.name }] }
  if (editing.value) {
    await useAuthFetch(`/api/v1/categories/${editing.value.id}/`, { method: 'PATCH', body })
  } else {
    await useAuthFetch('/api/v1/categories/', { method: 'POST', body })
  }
  dialog.value = false
  await load()
}

async function remove(cat: CategoryRow) {
  if (!confirm(`Delete category "${cat.name}"?`)) return
  await useAuthFetch(`/api/v1/categories/${cat.id}/`, { method: 'DELETE' })
  await load()
}

onMounted(load)
useSeoMeta({ title: 'Categories — CMS Admin' })
</script>

<template>
  <div>
    <div class="flex items-center justify-between">
      <div>
        <NuxtLink to="/admin/posts" class="text-sm" style="color: var(--text-faint)">&larr; Posts</NuxtLink>
        <h1 class="text-2xl font-black">Categories</h1>
      </div>
      <v-btn color="primary" @click="openCreate">New category</v-btn>
    </div>

    <p v-if="loading" class="mt-6 text-sm" style="color: var(--text-faint)">Loading…</p>
    <ul v-else class="mt-6 divide-y rounded-lg border" style="border-color: var(--border); background: var(--surface)">
      <li v-if="!categories.length" class="px-4 py-6 text-sm" style="color: var(--text-faint)">No categories yet.</li>
      <li v-for="cat in categories" :key="cat.id" class="flex items-center justify-between px-4 py-3">
        <div>
          <div class="font-semibold">{{ cat.name }}</div>
          <div class="text-xs" style="color: var(--text-faint)">/{{ cat.slug }}</div>
        </div>
        <div class="flex items-center gap-3">
          <button class="text-xs font-semibold" style="color: var(--info)" @click="openEdit(cat)">Edit</button>
          <button class="text-xs" style="color: var(--error)" @click="remove(cat)">Delete</button>
        </div>
      </li>
    </ul>

    <v-dialog v-model="dialog" max-width="420">
      <v-card :title="editing ? 'Edit category' : 'New category'">
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
