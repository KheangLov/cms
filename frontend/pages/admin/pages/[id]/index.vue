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
const pageId = route.params.id as string
const { t } = useI18n()

// Which locale variant of *translatable* block-prop fields the props panel
// currently shows/edits — independent of the admin's own UI language,
// since an English-speaking editor still needs to author the Khmer copy
// and vice versa.
const propLocale = ref<'en' | 'km'>('en')

const page = ref<any>(null)
const blockTypes = ref<BlockType[]>([])
const blocks = ref<BlockNode[]>([])
const selectedBlockId = ref<number | null>(null)
const saveStatus = ref('')

const settingsOpen = ref(false)
const settingsForm = reactive({ container_width: 'default', background_color: '', background_image_url: '' })
const CONTAINER_WIDTH_OPTIONS = computed(() => [
  { title: t('blockBuilder.containerNarrow'), value: 'narrow' },
  { title: t('blockBuilder.containerDefault'), value: 'default' },
  { title: t('blockBuilder.containerWide'), value: 'wide' },
  { title: t('blockBuilder.containerFull'), value: 'full' },
])

function openSettings() {
  settingsForm.container_width = page.value?.container_width || 'default'
  settingsForm.background_color = page.value?.background_color || ''
  settingsForm.background_image_url = page.value?.background_image_url || ''
  settingsOpen.value = true
}

async function saveSettings() {
  const updated = await useAuthFetch<any>(`/api/v1/pages/${pageId}/`, { method: 'PATCH', body: { ...settingsForm } })
  Object.assign(page.value, updated)
  settingsOpen.value = false
}

async function loadPage() {
  page.value = await useAuthFetch<any>(`/api/v1/pages/${pageId}/`)
  blocks.value = [...(page.value.blocks || [])].sort((a: BlockNode, b: BlockNode) => a.order - b.order)
}

async function loadBlockTypes() {
  const resp = await useAuthFetch<{ results: BlockType[] } | BlockType[]>('/api/v1/block-types/')
  blockTypes.value = Array.isArray(resp) ? resp : resp.results
}

// PageType.allowed_block_types is empty for every page type by default (no
// restriction — full block list). Filtering here is a convenience; the actual
// enforcement is server-side in PageBlockSerializer.validate, so a direct API
// call can't bypass this palette filter.
const availableBlockTypes = computed(() => {
  const allowed: number[] = page.value?.page_type?.allowed_block_types
  if (!allowed || allowed.length === 0) return blockTypes.value
  return blockTypes.value.filter((bt) => allowed.includes(bt.id))
})

async function togglePublish() {
  if (!page.value) return
  const action = page.value.status === 'published' ? 'unpublish' : 'publish'
  await useAuthFetch(`/api/v1/pages/${pageId}/${action}/`, { method: 'POST' })
  await loadPage()
}

onMounted(async () => {
  await Promise.all([loadPage(), loadBlockTypes()])
})

const selectedBlock = computed(() => blocks.value.find((b) => b.id === selectedBlockId.value) || null)

const { ensureReferenceOptions, optionsFor } = useReferenceOptions()
watch(selectedBlock, (block) => {
  for (const field of block?.block_type.prop_schema.fields || []) {
    if (field.type === 'reference') ensureReferenceOptions(field.referenceType)
  }
})

async function addBlock(blockType: BlockType) {
  const created = await useAuthFetch<BlockNode>('/api/v1/page-blocks/', {
    method: 'POST',
    body: { page: pageId, block_type: blockType.id, order: blocks.value.length, props: {} },
  })
  blocks.value.push({ ...created, block_type: blockType, children: [] })
  selectedBlockId.value = created.id
}

async function onReorder() {
  const payload = blocks.value.map((b, i) => ({ id: b.id, order: i, parent: null }))
  await useAuthFetch('/api/v1/page-blocks/reorder/', { method: 'POST', body: payload })
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
  await useAuthFetch(`/api/v1/page-blocks/${selectedBlock.value.id}/`, {
    method: 'PATCH',
    body: { props: selectedBlock.value.props },
  })
  saveStatus.value = 'saved'
  setTimeout(() => (saveStatus.value = ''), 1500)
}

async function removeBlock(block: BlockNode) {
  await useAuthFetch(`/api/v1/page-blocks/${block.id}/`, { method: 'DELETE' })
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

useSeoMeta({ title: 'Page Builder — CMS Admin' })
</script>

<template>
  <div class="flex flex-col" style="height: calc(100vh - 4rem)">
    <header class="flex items-center justify-between border-b px-4 py-2" style="border-color: var(--border)">
      <NuxtLink to="/admin/pages" class="flex items-center gap-1 text-sm" style="color: var(--text-faint)">
        <Icon name="solar:alt-arrow-left-linear" size="0.95rem" /> {{ $t('pagesAdmin.title') }}
      </NuxtLink>
      <h1 class="text-sm font-bold">{{ page?.slug }}</h1>
      <div class="flex items-center gap-2">
        <span
          class="rounded-full px-2 py-0.5 text-xs font-semibold capitalize"
          :style="
            page?.status === 'published'
              ? 'background: var(--success-bg); color: var(--success)'
              : 'background: var(--surface-2); color: var(--text-faint)'
          "
        >
          {{ page ? $t(`status.${page.status}`) : '' }}
        </span>
        <button
          class="bento-icon-btn"
          :title="page?.status === 'published' ? $t('blockBuilder.unpublish') : $t('blockBuilder.publish')"
          @click="togglePublish"
        >
          <Icon
            :name="page?.status === 'published' ? 'solar:eye-closed-bold-duotone' : 'solar:global-bold-duotone'"
            size="1rem"
          />
        </button>
        <a
          v-if="page?.status === 'published'"
          :href="`/${page.full_path}`"
          target="_blank"
          rel="noopener"
          class="bento-icon-btn"
          :title="$t('blockBuilder.openLivePage')"
        >
          <Icon name="solar:square-top-down-bold-duotone" size="1rem" />
        </a>
        <button class="bento-icon-btn" :title="$t('blockBuilder.pageSettingsTooltip')" @click="openSettings">
          <Icon name="solar:settings-bold-duotone" size="1rem" />
        </button>
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
        <p
          v-if="availableBlockTypes.length < blockTypes.length"
          class="mt-1 text-xs"
          style="color: var(--text-faint)"
        >
          {{ $t('blockBuilder.allowedCount', { shown: availableBlockTypes.length, total: blockTypes.length }) }}
        </p>
        <button
          v-for="bt in availableBlockTypes"
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

      <!-- Props panel -->
      <aside class="w-72 shrink-0 overflow-y-auto border-l p-4" style="border-color: var(--border)">
        <template v-if="selectedBlock">
          <h2 class="flex items-center gap-1.5 text-xs font-bold uppercase" style="color: var(--text-faint)">
            <Icon :name="iconForBlockType(selectedBlock.block_type.slug)" size="1rem" />
            {{ selectedBlock.block_type.name }} {{ $t('blockBuilder.props') }}
          </h2>

          <div v-if="selectedBlock.block_type.prop_schema.fields.some((f) => f.translatable)" class="bento-pill-group mt-3">
            <button class="bento-pill" :class="{ 'bento-pill--active': propLocale === 'en' }" @click="propLocale = 'en'">EN</button>
            <button class="bento-pill" :class="{ 'bento-pill--active': propLocale === 'km' }" @click="propLocale = 'km'">ខ្មែរ</button>
          </div>

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
        <p v-else class="text-sm" style="color: var(--text-faint)">{{ $t('blockBuilder.selectBlockHint') }}</p>
      </aside>
    </div>

    <v-dialog v-model="settingsOpen" max-width="480">
      <div class="bento-card p-5">
        <h2 class="text-sm font-bold">{{ $t('blockBuilder.pageSettingsTitle') }}</h2>
        <p class="mt-1 text-xs" style="color: var(--text-faint)">
          {{ $t('blockBuilder.pageSettingsSubtitle') }}
        </p>
        <v-select
          v-model="settingsForm.container_width"
          :items="CONTAINER_WIDTH_OPTIONS"
          :label="$t('blockBuilder.containerWidth')"
          class="mt-4"
          hide-details
          density="compact"
        />
        <v-text-field
          v-model="settingsForm.background_color"
          :label="$t('blockBuilder.backgroundColor')"
          placeholder="#0f172a or linear-gradient(...)"
          class="mt-3"
          hide-details
          density="compact"
        />
        <v-text-field
          v-model="settingsForm.background_image_url"
          :label="$t('blockBuilder.backgroundImageUrl')"
          class="mt-3"
          hide-details
          density="compact"
        />
        <div class="mt-5 flex justify-end gap-2">
          <v-btn variant="text" @click="settingsOpen = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="primary" @click="saveSettings">{{ $t('common.save') }}</v-btn>
        </div>
      </div>
    </v-dialog>
  </div>
</template>
