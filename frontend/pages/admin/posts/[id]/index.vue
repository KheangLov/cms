<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth', fullBleed: true })

import draggable from 'vuedraggable'

interface PropField {
  key: string
  type: string
  label: string
  translatable?: boolean
  itemFields?: PropField[]
  referenceType?: string
}

interface BlockType {
  id: number
  name: string
  slug: string
  prop_schema: { fields: PropField[] }
}

interface BlockNode {
  id: number
  block_type: BlockType
  order: number
  props: Record<string, any>
  children: BlockNode[]
}

const route = useRoute()
const postId = route.params.id as string
const { t } = useI18n()

// Which locale variant of translatable content (block props + this post's
// excerpt) the sidebar currently shows/edits — see pages/[id]/index.vue's
// identical propLocale for the full rationale.
const propLocale = ref<'en' | 'km'>('en')

const post = ref<any>(null)
const blockTypes = ref<BlockType[]>([])
const blocks = ref<BlockNode[]>([])
const selectedBlockId = ref<number | null>(null)
const saveStatus = ref('')

// WordPress-inspired: the right sidebar is either the "Document" panel (category,
// tags, featured image, excerpt, status — always available) or the selected
// block's props. Selecting a block switches to it automatically, matching how
// WordPress's own Post/Block tabs behave.
const sidebarTab = ref<'post' | 'block'>('post')
watch(selectedBlockId, (id) => {
  if (id !== null) sidebarTab.value = 'block'
})

interface Category {
  id: number
  name: string
}
interface Tag {
  id: number
  name: string
}
interface MediaRow {
  id: number
  original_filename: string
  thumbnail_small: string | null
  mime_type: string
}

const categories = ref<Category[]>([])
const tags = ref<Tag[]>([])
const newTagName = ref('')
const creatingTag = ref(false)

const postCategory = ref<number | null>(null)
const postTagIds = ref<number[]>([])
const excerptByLocale = reactive<Record<string, string>>({ en: '', km: '' })
const featuredImageId = ref<number | null>(null)
const featuredImagePreview = ref<string | null>(null)
const containerWidth = ref('default')
const backgroundColor = ref('')
const backgroundImageUrl = ref('')
const CONTAINER_WIDTH_OPTIONS = computed(() => [
  { title: t('blockBuilder.containerNarrow'), value: 'narrow' },
  { title: t('blockBuilder.containerDefault'), value: 'default' },
  { title: t('blockBuilder.containerWide'), value: 'wide' },
  { title: t('blockBuilder.containerFull'), value: 'full' },
])

const savingMeta = ref(false)
const metaSaved = ref(false)

const pickerOpen = ref(false)
const pickerMedia = ref<MediaRow[]>([])

async function loadPost() {
  post.value = await useAuthFetch<any>(`/api/v1/posts/${postId}/`)
  blocks.value = [...(post.value.blocks || [])].sort((a: BlockNode, b: BlockNode) => a.order - b.order)

  postCategory.value = post.value.category?.id ?? null
  postTagIds.value = (post.value.tags || []).map((t: Tag) => t.id)
  const translations = post.value.translations || []
  excerptByLocale.en = translations.find((tr: any) => tr.locale === 'en')?.excerpt || ''
  excerptByLocale.km = translations.find((tr: any) => tr.locale === 'km')?.excerpt || ''
  containerWidth.value = post.value.container_width || 'default'
  backgroundColor.value = post.value.background_color || ''
  backgroundImageUrl.value = post.value.background_image_url || ''

  // PostDetailSerializer nests category/tags but leaves featured_image as a plain
  // FK id (only category/tags/blocks are overridden to nest) — so the thumbnail
  // needs its own lookup rather than reading it straight off `post.value`.
  featuredImageId.value = post.value.featured_image ?? null
  featuredImagePreview.value = null
  if (featuredImageId.value) {
    try {
      const media = await useAuthFetch<MediaRow>(`/api/v1/media/${featuredImageId.value}/`)
      featuredImagePreview.value = media.thumbnail_small
    } catch {
      // media may have been hard-deleted independently of the post; not fatal
    }
  }
}

async function loadBlockTypes() {
  const resp = await useAuthFetch<{ results: BlockType[] } | BlockType[]>('/api/v1/block-types/')
  blockTypes.value = Array.isArray(resp) ? resp : resp.results
}

async function loadTaxonomy() {
  const [catResp, tagResp] = await Promise.all([
    useAuthFetch<{ results: Category[] } | Category[]>('/api/v1/categories/'),
    useAuthFetch<{ results: Tag[] } | Tag[]>('/api/v1/tags/'),
  ])
  categories.value = Array.isArray(catResp) ? catResp : catResp.results
  tags.value = Array.isArray(tagResp) ? tagResp : tagResp.results
}

onMounted(async () => {
  await Promise.all([loadPost(), loadBlockTypes(), loadTaxonomy()])
})

function slugify(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '')
}

async function quickCreateTag() {
  const name = newTagName.value.trim()
  if (!name) return
  creatingTag.value = true
  try {
    const created = await useAuthFetch<Tag>('/api/v1/tags/', {
      method: 'POST',
      body: { name, slug: slugify(name), translations: [{ locale: 'en', name }] },
    })
    tags.value.push(created)
    postTagIds.value.push(created.id)
    newTagName.value = ''
  } finally {
    creatingTag.value = false
  }
}

async function openPicker() {
  pickerOpen.value = true
  const resp = await useAuthFetch<{ results: MediaRow[] } | MediaRow[]>('/api/v1/media/?trash=0')
  const all = Array.isArray(resp) ? resp : resp.results
  pickerMedia.value = all.filter((m) => m.mime_type.startsWith('image/'))
}

function selectFeaturedImage(media: MediaRow) {
  featuredImageId.value = media.id
  featuredImagePreview.value = media.thumbnail_small
  pickerOpen.value = false
}

function removeFeaturedImage() {
  featuredImageId.value = null
  featuredImagePreview.value = null
}

async function togglePublish() {
  if (!post.value) return
  const action = post.value.status === 'published' ? 'unpublish' : 'publish'
  await useAuthFetch(`/api/v1/posts/${postId}/${action}/`, { method: 'POST' })
  await loadPost()
}

async function saveMeta() {
  savingMeta.value = true
  metaSaved.value = false
  try {
    const existing = post.value.translations || []
    // Every locale with a non-empty excerpt gets a translation row — existing
    // rows keep their title/meta as-is (this panel doesn't edit those), a
    // locale with no row yet (e.g. first time authoring the km excerpt) gets
    // a minimal one seeded from the slug, same fallback the original en-only
    // version of this code already used.
    const translations = ['en', 'km'].flatMap((loc) => {
      const row = existing.find((tr: any) => tr.locale === loc)
      if (row) return [{ ...row, excerpt: excerptByLocale[loc] }]
      if (excerptByLocale[loc]) {
        return [{ locale: loc, title: post.value.slug, excerpt: excerptByLocale[loc], meta_title: '', meta_description: '' }]
      }
      return []
    })

    await useAuthFetch(`/api/v1/posts/${postId}/`, {
      method: 'PATCH',
      body: {
        category: postCategory.value,
        tags: postTagIds.value,
        featured_image: featuredImageId.value,
        container_width: containerWidth.value,
        background_color: backgroundColor.value,
        background_image_url: backgroundImageUrl.value,
        translations,
      },
    })
    await loadPost()
    metaSaved.value = true
    setTimeout(() => (metaSaved.value = false), 2000)
  } finally {
    savingMeta.value = false
  }
}

const selectedBlock = computed(() => blocks.value.find((b) => b.id === selectedBlockId.value) || null)

const { ensureReferenceOptions, optionsFor } = useReferenceOptions()
watch(selectedBlock, (block) => {
  for (const field of block?.block_type.prop_schema.fields || []) {
    if (field.type === 'reference') ensureReferenceOptions(field.referenceType)
  }
})

async function addBlock(blockType: BlockType) {
  const created = await useAuthFetch<BlockNode>('/api/v1/post-blocks/', {
    method: 'POST',
    body: { post: postId, block_type: blockType.id, order: blocks.value.length, props: {} },
  })
  blocks.value.push({ ...created, block_type: blockType, children: [] })
  selectedBlockId.value = created.id
}

async function onReorder() {
  const payload = blocks.value.map((b, i) => ({ id: b.id, order: i, parent: null }))
  await useAuthFetch('/api/v1/post-blocks/reorder/', { method: 'POST', body: payload })
}

function updateProp(key: string, value: unknown, locale?: string) {
  if (!selectedBlock.value) return
  if (locale) {
    selectedBlock.value.props[key] = { ...(selectedBlock.value.props[key] || {}), [locale]: value }
  } else {
    selectedBlock.value.props[key] = value
  }
}

async function saveSelectedBlock() {
  if (!selectedBlock.value) return
  saveStatus.value = 'saving'
  await useAuthFetch(`/api/v1/post-blocks/${selectedBlock.value.id}/`, {
    method: 'PATCH',
    body: { props: selectedBlock.value.props },
  })
  saveStatus.value = 'saved'
  setTimeout(() => (saveStatus.value = ''), 1500)
}

async function removeBlock(block: BlockNode) {
  await useAuthFetch(`/api/v1/post-blocks/${block.id}/`, { method: 'DELETE' })
  blocks.value = blocks.value.filter((b) => b.id !== block.id)
  if (selectedBlockId.value === block.id) selectedBlockId.value = null
}

const blockTypeIcon: Record<string, string> = {
  hero: 'solar:gallery-wide-bold-duotone',
  'text-section': 'solar:align-left-bold-duotone',
  swiper: 'solar:slider-horizontal-bold-duotone',
  columns: 'solar:widget-4-bold-duotone',
  posts: 'solar:notes-bold-duotone',
}

function iconForBlockType(slug: string): string {
  return blockTypeIcon[slug] || 'solar:widget-5-bold-duotone'
}

function rawPropsText(block: BlockNode): string {
  return JSON.stringify(block.props, null, 2)
}

function setRawProps(block: BlockNode, text: string) {
  try {
    block.props = JSON.parse(text)
  } catch {
    // leave as-is until valid JSON — this is the advanced/escape-hatch editor
  }
}

useSeoMeta({ title: 'Post Builder — CMS Admin' })
</script>

<template>
  <div class="flex flex-col" style="height: calc(100vh - 4rem)">
    <header class="flex items-center justify-between border-b px-4 py-2" style="border-color: var(--border)">
      <NuxtLink to="/admin/posts" class="flex items-center gap-1 text-sm" style="color: var(--text-faint)">
        <Icon name="solar:alt-arrow-left-linear" size="0.95rem" /> {{ $t('postsAdmin.title') }}
      </NuxtLink>
      <h1 class="text-sm font-bold">{{ post?.slug }}</h1>
      <div class="flex items-center gap-2">
        <span
          class="rounded-full px-2 py-0.5 text-xs font-semibold capitalize"
          :style="
            post?.status === 'published'
              ? 'background: var(--success-bg); color: var(--success)'
              : 'background: var(--surface-2); color: var(--text-faint)'
          "
        >
          {{ post ? $t(`status.${post.status}`) : '' }}
        </span>
        <button
          class="bento-icon-btn"
          :title="post?.status === 'published' ? $t('blockBuilder.unpublish') : $t('blockBuilder.publish')"
          @click="togglePublish"
        >
          <Icon
            :name="post?.status === 'published' ? 'solar:eye-closed-bold-duotone' : 'solar:global-bold-duotone'"
            size="1rem"
          />
        </button>
        <a
          v-if="post?.status === 'published'"
          :href="`/post/${post.slug}`"
          target="_blank"
          rel="noopener"
          class="bento-icon-btn"
          :title="$t('postsAdmin.openLivePost')"
        >
          <Icon name="solar:square-top-down-bold-duotone" size="1rem" />
        </a>
        <span class="flex items-center gap-1 text-xs" style="color: var(--text-faint)">
          <Icon v-if="saveStatus === 'saved'" name="solar:check-circle-bold-duotone" size="0.95rem" style="color: var(--success)" />
          {{ saveStatus === 'saving' ? $t('blockBuilder.saving') : saveStatus === 'saved' ? $t('blockBuilder.saved') : '' }}
        </span>
      </div>
    </header>

    <div class="flex min-h-0 flex-1">
      <!-- Palette -->
      <aside class="w-56 shrink-0 overflow-y-auto border-r p-4" style="border-color: var(--border)">
        <h2 class="text-xs font-bold uppercase" style="color: var(--text-faint)">{{ $t('blockBuilder.addBlock') }}</h2>
        <button
          v-for="bt in blockTypes"
          :key="bt.id"
          class="bento-card mt-2 flex w-full items-center gap-2 px-3 py-2 text-left text-sm"
          @click="addBlock(bt)"
        >
          <span class="bento-row__icon" style="width: 1.8rem; height: 1.8rem; font-size: 1rem">
            <Icon :name="iconForBlockType(bt.slug)" />
          </span>
          {{ bt.name }}
        </button>
      </aside>

      <!-- Canvas -->
      <main class="flex-1 overflow-y-auto p-6" style="background: var(--surface-2)">
        <p v-if="!blocks.length" class="text-sm" style="color: var(--text-faint)">
          {{ $t('blockBuilder.noBlocksYet') }}
        </p>
        <draggable v-model="blocks" item-key="id" class="space-y-3" handle=".drag-handle" @end="onReorder">
          <template #item="{ element }">
            <div
              class="bento-card cursor-pointer p-2"
              :style="{ borderColor: selectedBlockId === element.id ? 'var(--ember)' : 'var(--border)' }"
              @click="selectedBlockId = element.id"
            >
              <div class="flex items-center justify-between px-2 py-1">
                <span class="drag-handle flex cursor-grab items-center gap-1.5 text-xs font-bold uppercase" style="color: var(--text-faint)">
                  <Icon name="solar:menu-dots-bold-duotone" size="0.95rem" />
                  <Icon :name="iconForBlockType(element.block_type.slug)" size="1rem" />
                  {{ element.block_type.name }}
                </span>
                <button class="bento-icon-btn bento-icon-btn--danger" :title="$t('blockBuilder.removeBlock')" @click.stop="removeBlock(element)">
                  <Icon name="solar:trash-bin-2-bold-duotone" size="0.95rem" />
                </button>
              </div>
              <BlocksBlockRenderer :blocks="[element]" :locale="propLocale" />
            </div>
          </template>
        </draggable>
      </main>

      <!-- Sidebar: Post (WordPress "Document" panel) / Block props -->
      <aside class="w-80 shrink-0 overflow-y-auto border-l p-4" style="border-color: var(--border)">
        <div class="flex items-center justify-between">
          <div class="bento-pill-group">
            <button class="bento-pill" :class="{ 'bento-pill--active': sidebarTab === 'post' }" @click="sidebarTab = 'post'">
              {{ $t('blockBuilder.postTab') }}
            </button>
            <button
              class="bento-pill"
              :class="{ 'bento-pill--active': sidebarTab === 'block' }"
              :disabled="!selectedBlock"
              :style="!selectedBlock ? 'opacity: 0.4; cursor: default' : ''"
              @click="selectedBlock && (sidebarTab = 'block')"
            >
              {{ $t('blockBuilder.blockTab') }}
            </button>
          </div>
          <div class="bento-pill-group">
            <button class="bento-pill" :class="{ 'bento-pill--active': propLocale === 'en' }" @click="propLocale = 'en'">EN</button>
            <button class="bento-pill" :class="{ 'bento-pill--active': propLocale === 'km' }" @click="propLocale = 'km'">ខ្មែរ</button>
          </div>
        </div>

        <div v-if="sidebarTab === 'post'" class="mt-4">
          <v-select
            v-model="postCategory"
            :items="categories"
            item-title="name"
            item-value="id"
            :label="$t('blockBuilder.category')"
            clearable
            hide-details
            density="compact"
          />

          <v-select
            v-model="postTagIds"
            :items="tags"
            item-title="name"
            item-value="id"
            :label="$t('blockBuilder.tags')"
            multiple
            chips
            hide-details
            density="compact"
            class="mt-3"
          />
          <div class="mt-2 flex gap-2">
            <v-text-field
              v-model="newTagName"
              :placeholder="$t('blockBuilder.newTagPlaceholder')"
              hide-details
              density="compact"
              @keyup.enter="quickCreateTag"
            />
            <v-btn size="small" :loading="creatingTag" @click="quickCreateTag">{{ $t('blockBuilder.add') }}</v-btn>
          </div>

          <div class="mt-4">
            <label class="block text-xs font-bold uppercase" style="color: var(--text-faint)">{{ $t('blockBuilder.featuredImage') }}</label>
            <div v-if="featuredImagePreview">
              <img
                :src="featuredImagePreview"
                alt=""
                class="mt-2 aspect-video w-full rounded-lg object-cover"
                style="border: 0.0625rem solid var(--border)"
              />
              <div class="mt-2 flex gap-2">
                <v-btn size="small" variant="tonal" @click="openPicker">{{ $t('blockBuilder.change') }}</v-btn>
                <v-btn size="small" variant="text" @click="removeFeaturedImage">{{ $t('blockBuilder.remove') }}</v-btn>
              </div>
            </div>
            <v-btn v-else variant="tonal" block class="mt-2" @click="openPicker">
              <Icon name="solar:gallery-add-bold-duotone" size="1.05rem" class="mr-1.5" />
              {{ $t('blockBuilder.setFeaturedImage') }}
            </v-btn>
          </div>

          <v-textarea v-model="excerptByLocale[propLocale]" :label="$t('blockBuilder.excerpt')" rows="3" hide-details density="compact" class="mt-4" />

          <h3 class="mt-5 text-xs font-bold uppercase" style="color: var(--text-faint)">{{ $t('blockBuilder.pageSettingsTitle') }}</h3>
          <v-select
            v-model="containerWidth"
            :items="CONTAINER_WIDTH_OPTIONS"
            :label="$t('blockBuilder.containerWidth')"
            class="mt-2"
            hide-details
            density="compact"
          />
          <v-text-field
            v-model="backgroundColor"
            :label="$t('blockBuilder.backgroundColor')"
            class="mt-3"
            hide-details
            density="compact"
          />
          <v-text-field
            v-model="backgroundImageUrl"
            :label="$t('blockBuilder.backgroundImageUrl')"
            class="mt-3"
            hide-details
            density="compact"
          />

          <v-btn color="primary" block class="mt-4" :loading="savingMeta" @click="saveMeta">
            <Icon name="solar:diskette-bold-duotone" size="1.05rem" class="mr-1.5" />
            {{ $t('blockBuilder.savePostDetails') }}
          </v-btn>
          <span
            v-if="metaSaved"
            class="mt-2 flex items-center justify-center gap-1 text-xs"
            style="color: var(--success)"
          >
            <Icon name="solar:check-circle-bold-duotone" size="0.9rem" /> {{ $t('blockBuilder.saved') }}
          </span>
        </div>

        <template v-else-if="selectedBlock">
          <h2 class="mt-4 flex items-center gap-1.5 text-xs font-bold uppercase" style="color: var(--text-faint)">
            <Icon :name="iconForBlockType(selectedBlock.block_type.slug)" size="1rem" />
            {{ selectedBlock.block_type.name }} {{ $t('blockBuilder.props') }}
          </h2>
          <div v-for="field in selectedBlock.block_type.prop_schema.fields" :key="field.key" class="mt-3">
            <label class="block text-xs font-semibold">{{ field.label }}</label>
            <textarea
              v-if="field.type === 'textarea'"
              class="bento-input mt-1"
              rows="3"
              :value="field.translatable ? selectedBlock.props[field.key]?.[propLocale] || '' : selectedBlock.props[field.key] || ''"
              @input="
                updateProp(
                  field.key,
                  ($event.target as HTMLTextAreaElement).value,
                  field.translatable ? propLocale : undefined,
                )
              "
            />
            <ListFieldEditor
              v-else-if="field.type === 'list'"
              class="mt-1"
              :model-value="selectedBlock.props[field.key] || []"
              :item-fields="field.itemFields || []"
              :locale="propLocale"
              @update:model-value="updateProp(field.key, $event)"
            />
            <RichTextEditor
              v-else-if="field.type === 'richtext'"
              class="mt-1"
              :model-value="field.translatable ? selectedBlock.props[field.key]?.[propLocale] || '' : selectedBlock.props[field.key] || ''"
              @update:model-value="updateProp(field.key, $event, field.translatable ? propLocale : undefined)"
            />
            <v-select
              v-else-if="field.type === 'reference'"
              class="mt-1"
              :items="optionsFor(field.referenceType)"
              item-title="title"
              item-value="id"
              hide-details
              density="compact"
              :model-value="selectedBlock.props[field.key] ?? null"
              @update:model-value="updateProp(field.key, $event)"
            />
            <input
              v-else
              class="bento-input mt-1"
              :value="field.translatable ? selectedBlock.props[field.key]?.[propLocale] || '' : selectedBlock.props[field.key] || ''"
              @input="
                updateProp(
                  field.key,
                  ($event.target as HTMLInputElement).value,
                  field.translatable ? propLocale : undefined,
                )
              "
            />
          </div>

          <details class="mt-4">
            <summary class="cursor-pointer text-xs" style="color: var(--text-faint)">{{ $t('blockBuilder.advancedRawJson') }}</summary>
            <textarea
              class="bento-input mt-2 font-mono text-xs"
              rows="6"
              :value="rawPropsText(selectedBlock)"
              @change="setRawProps(selectedBlock, ($event.target as HTMLTextAreaElement).value)"
            />
          </details>

          <v-btn color="primary" block class="mt-4" @click="saveSelectedBlock">
            <Icon name="solar:diskette-bold-duotone" size="1.05rem" class="mr-1.5" />
            {{ $t('blockBuilder.saveBlock') }}
          </v-btn>
        </template>
        <p v-else class="mt-4 text-sm" style="color: var(--text-faint)">{{ $t('blockBuilder.selectBlockHint') }}</p>
      </aside>
    </div>

    <v-dialog v-model="pickerOpen" max-width="640">
      <v-card :title="$t('blockBuilder.chooseFeaturedImage')">
        <v-card-text>
          <p v-if="!pickerMedia.length" class="text-sm" style="color: var(--text-faint)">
            {{ $t('blockBuilder.noImagesYet') }}
          </p>
          <div v-else class="grid grid-cols-4 gap-3">
            <button
              v-for="m in pickerMedia"
              :key="m.id"
              class="bento-card overflow-hidden"
              type="button"
              @click="selectFeaturedImage(m)"
            >
              <img
                v-if="m.thumbnail_small"
                :src="m.thumbnail_small"
                :alt="m.original_filename"
                class="aspect-square w-full object-cover"
              />
              <div v-else class="flex aspect-square items-center justify-center" style="background: var(--surface-2)">
                <Icon name="solar:file-bold-duotone" size="1.5rem" style="color: var(--text-faint)" />
              </div>
            </button>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="pickerOpen = false">{{ $t('common.cancel') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
