<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'auth', fullBleed: true })

import draggable from 'vuedraggable'

interface PropField {
  key: string
  type: string
  label: string
  translatable?: boolean
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

const post = ref<any>(null)
const blockTypes = ref<BlockType[]>([])
const blocks = ref<BlockNode[]>([])
const selectedBlockId = ref<number | null>(null)
const saveStatus = ref('')

async function loadPost() {
  post.value = await useAuthFetch<any>(`/api/v1/posts/${postId}/`)
  blocks.value = [...(post.value.blocks || [])].sort((a: BlockNode, b: BlockNode) => a.order - b.order)
}

async function loadBlockTypes() {
  const resp = await useAuthFetch<{ results: BlockType[] } | BlockType[]>('/api/v1/block-types/')
  blockTypes.value = Array.isArray(resp) ? resp : resp.results
}

onMounted(async () => {
  await Promise.all([loadPost(), loadBlockTypes()])
})

const selectedBlock = computed(() => blocks.value.find((b) => b.id === selectedBlockId.value) || null)

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
  saveStatus.value = 'Saving…'
  await useAuthFetch(`/api/v1/post-blocks/${selectedBlock.value.id}/`, {
    method: 'PATCH',
    body: { props: selectedBlock.value.props },
  })
  saveStatus.value = 'Saved'
  setTimeout(() => (saveStatus.value = ''), 1500)
}

async function removeBlock(block: BlockNode) {
  await useAuthFetch(`/api/v1/post-blocks/${block.id}/`, { method: 'DELETE' })
  blocks.value = blocks.value.filter((b) => b.id !== block.id)
  if (selectedBlockId.value === block.id) selectedBlockId.value = null
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
      <NuxtLink to="/admin/posts" class="text-sm" style="color: var(--text-faint)">&larr; Posts</NuxtLink>
      <h1 class="text-sm font-bold">{{ post?.slug }}</h1>
      <span class="text-xs" style="color: var(--text-faint)">{{ saveStatus }}</span>
    </header>

    <div class="flex min-h-0 flex-1">
      <!-- Palette -->
      <aside class="w-56 shrink-0 overflow-y-auto border-r p-4" style="border-color: var(--border)">
        <h2 class="text-xs font-bold uppercase" style="color: var(--text-faint)">Add block</h2>
        <button
          v-for="bt in blockTypes"
          :key="bt.id"
          class="mt-2 block w-full rounded border px-3 py-2 text-left text-sm"
          style="border-color: var(--border)"
          @click="addBlock(bt)"
        >
          {{ bt.name }}
        </button>
      </aside>

      <!-- Canvas -->
      <main class="flex-1 overflow-y-auto p-6" style="background: var(--surface-2)">
        <p v-if="!blocks.length" class="text-sm" style="color: var(--text-faint)">
          No blocks yet — add one from the palette on the left.
        </p>
        <draggable v-model="blocks" item-key="id" class="space-y-3" handle=".drag-handle" @end="onReorder">
          <template #item="{ element }">
            <div
              class="cursor-pointer rounded-lg border-2 p-2"
              :style="{
                background: 'var(--surface)',
                borderColor: selectedBlockId === element.id ? 'var(--ember)' : 'transparent',
              }"
              @click="selectedBlockId = element.id"
            >
              <div class="flex items-center justify-between px-2 py-1">
                <span class="drag-handle cursor-grab text-xs font-bold uppercase" style="color: var(--text-faint)">
                  ⠿ {{ element.block_type.name }}
                </span>
                <button class="text-xs" style="color: var(--error)" @click.stop="removeBlock(element)">Remove</button>
              </div>
              <BlocksBlockRenderer :blocks="[element]" locale="en" />
            </div>
          </template>
        </draggable>
      </main>

      <!-- Props panel -->
      <aside class="w-72 shrink-0 overflow-y-auto border-l p-4" style="border-color: var(--border)">
        <template v-if="selectedBlock">
          <h2 class="text-xs font-bold uppercase" style="color: var(--text-faint)">
            {{ selectedBlock.block_type.name }} props
          </h2>
          <div v-for="field in selectedBlock.block_type.prop_schema.fields" :key="field.key" class="mt-3">
            <label class="block text-xs font-semibold">{{ field.label }}</label>
            <textarea
              v-if="field.type === 'textarea'"
              class="mt-1 w-full rounded border px-2 py-1 text-sm"
              style="border-color: var(--border)"
              rows="3"
              :value="field.translatable ? selectedBlock.props[field.key]?.en || '' : selectedBlock.props[field.key] || ''"
              @input="
                updateProp(
                  field.key,
                  ($event.target as HTMLTextAreaElement).value,
                  field.translatable ? 'en' : undefined,
                )
              "
            />
            <input
              v-else-if="field.type !== 'list'"
              class="mt-1 w-full rounded border px-2 py-1 text-sm"
              style="border-color: var(--border)"
              :value="field.translatable ? selectedBlock.props[field.key]?.en || '' : selectedBlock.props[field.key] || ''"
              @input="
                updateProp(
                  field.key,
                  ($event.target as HTMLInputElement).value,
                  field.translatable ? 'en' : undefined,
                )
              "
            />
            <p v-else class="mt-1 text-xs" style="color: var(--text-faint)">
              Edit "{{ field.label }}" via the advanced JSON editor below.
            </p>
          </div>

          <details class="mt-4">
            <summary class="cursor-pointer text-xs" style="color: var(--text-faint)">Advanced: raw JSON</summary>
            <textarea
              class="mt-2 w-full rounded border px-2 py-1 font-mono text-xs"
              style="border-color: var(--border)"
              rows="6"
              :value="rawPropsText(selectedBlock)"
              @change="setRawProps(selectedBlock, ($event.target as HTMLTextAreaElement).value)"
            />
          </details>

          <v-btn color="primary" block class="mt-4" @click="saveSelectedBlock">Save block</v-btn>
        </template>
        <p v-else class="text-sm" style="color: var(--text-faint)">Select a block to edit its properties.</p>
      </aside>
    </div>
  </div>
</template>
