<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth' })

const { confirm } = useConfirmDialog()
const { t } = useI18n()

interface TagRow {
  id: number
  name: string
  slug: string
}

const dialog = ref(false)
const editing = ref<TagRow | null>(null)
const form = reactive({ name: '', slug: '' })

const { items: tags, loading, loadingMore, hasMore, load, loadMore } = useInfiniteList<TagRow>(() => '/api/v1/tags/')
const sentinel = useInfiniteScrollSentinel(loadMore)

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
  if (!(await confirm({ message: t('tagsAdmin.deleteConfirm', { name: tag.name }), danger: true }))) return
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
        <h1 class="text-2xl font-black">{{ $t('tagsAdmin.title') }}</h1>
      </div>
      <v-btn color="primary" @click="openCreate">
        <Icon name="solar:add-circle-bold-duotone" size="1.05rem" class="mr-1.5" />
        {{ $t('tagsAdmin.newTag') }}
      </v-btn>
    </div>

    <p v-if="loading" class="mt-6 text-sm" style="color: var(--text-faint)">{{ $t('common.loading') }}</p>
    <div v-else class="bento-card mt-6">
      <p v-if="!tags.length" class="px-4 py-6 text-sm" style="color: var(--text-faint)">{{ $t('tagsAdmin.noTagsYet') }}</p>
      <div v-for="tag in tags" :key="tag.id" class="bento-row">
        <span class="bento-row__icon"><Icon name="solar:tag-bold-duotone" /></span>
        <div class="bento-row__body">
          <div class="font-semibold">{{ tag.name }}</div>
          <div class="text-xs" style="color: var(--text-faint)">/{{ tag.slug }}</div>
        </div>
        <div class="bento-row__actions">
          <button class="bento-icon-btn bento-icon-btn--primary" :title="$t('common.edit')" @click="openEdit(tag)">
            <Icon name="solar:pen-2-bold-duotone" />
          </button>
          <button class="bento-icon-btn bento-icon-btn--danger" :title="$t('common.delete')" @click="remove(tag)">
            <Icon name="solar:trash-bin-2-bold-duotone" />
          </button>
        </div>
      </div>
      <div v-if="tags.length" ref="sentinel" class="flex justify-center py-4">
        <span v-if="loadingMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.loadingMore') }}</span>
        <span v-else-if="!hasMore" class="text-xs" style="color: var(--text-faint)">{{ $t('common.endOfList') }}</span>
      </div>
    </div>

    <v-dialog v-model="dialog" max-width="420">
      <v-card :title="editing ? $t('tagsAdmin.editTag') : $t('tagsAdmin.newTag')">
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
