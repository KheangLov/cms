<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

const { confirm } = useConfirmDialog()
const { t } = useI18n()

interface CategoryRow {
  id: number
  name: string
  slug: string
  parent: number | null
}

const dialog = ref(false)
const editing = ref<CategoryRow | null>(null)
const form = reactive({ name: '', slug: '' })

const { items: categories, loading, loadingMore, hasMore, load, loadMore } = useInfiniteList<CategoryRow>(
  () => '/api/v1/categories/',
)
const sentinel = useInfiniteScrollSentinel(loadMore)

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
  if (!(await confirm({ message: t('categoriesAdmin.deleteConfirm', { name: cat.name }), danger: true }))) return
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
        <h1 class="text-2xl font-black">{{ $t('categoriesAdmin.title') }}</h1>
      </div>
      <v-btn color="primary" @click="openCreate">
        <Icon name="solar:add-circle-bold-duotone" size="1.05rem" class="mr-1.5" />
        {{ $t('categoriesAdmin.newCategory') }}
      </v-btn>
    </div>

    <p v-if="loading" class="mt-6 text-sm" style="color: var(--text-faint)">{{ $t('common.loading') }}</p>
    <div v-else class="bento-card mt-6">
      <p v-if="!categories.length" class="px-4 py-6 text-sm" style="color: var(--text-faint)">{{ $t('categoriesAdmin.noCategoriesYet') }}</p>
      <div v-for="cat in categories" :key="cat.id" class="bento-row">
        <span class="bento-row__icon"><Icon name="solar:folder-bold-duotone" /></span>
        <div class="bento-row__body">
          <div class="font-semibold">{{ cat.name }}</div>
          <div class="text-xs" style="color: var(--text-faint)">/{{ cat.slug }}</div>
        </div>
        <div class="bento-row__actions">
          <button class="bento-icon-btn bento-icon-btn--primary" :title="$t('common.edit')" @click="openEdit(cat)">
            <Icon name="solar:pen-2-bold-duotone" />
          </button>
          <button class="bento-icon-btn bento-icon-btn--danger" :title="$t('common.delete')" @click="remove(cat)">
            <Icon name="solar:trash-bin-2-bold-duotone" />
          </button>
        </div>
      </div>
      <div v-if="categories.length" ref="sentinel" class="flex justify-center py-4">
        <span v-if="loadingMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.loadingMore') }}</span>
        <span v-else-if="!hasMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.endOfList') }}</span>
      </div>
    </div>

    <v-dialog v-model="dialog" max-width="420">
      <v-card :title="editing ? $t('categoriesAdmin.editCategory') : $t('categoriesAdmin.newCategory')">
        <v-card-text class="flex flex-col gap-3">
          <v-text-field v-model="form.name" :label="$t('common.name')" hide-details density="compact" />
          <v-text-field v-model="form.slug" :label="$t('common.slug')" hide-details density="compact" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="primary" variant="elevated" @click="save">{{ $t('common.save') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
