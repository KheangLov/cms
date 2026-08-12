<script setup lang="ts">
import ColumnsBlock from './ColumnsBlock.vue'
import HeroBlock from './HeroBlock.vue'
import SwiperBlock from './SwiperBlock.vue'
import TextSectionBlock from './TextSectionBlock.vue'

interface BlockNode {
  id: number
  block_type: { slug: string; name: string }
  order: number
  props: Record<string, any>
  children: BlockNode[]
}

defineProps<{
  blocks: BlockNode[]
  locale?: string
}>()

// CMS_BUILD_PROMPT.md §5.2 — the same map (and the same components) render both
// the builder canvas and the public page. Adding a block type = a registry row
// (apps/blocks migrations) + a Vue component + one line here.
const componentMap: Record<string, unknown> = {
  hero: HeroBlock,
  'text-section': TextSectionBlock,
  swiper: SwiperBlock,
  columns: ColumnsBlock,
}
</script>

<template>
  <template v-for="block in blocks" :key="block.id">
    <component
      :is="componentMap[block.block_type.slug]"
      v-if="componentMap[block.block_type.slug]"
      :block="block"
      :locale="locale || 'en'"
    />
    <div v-else class="rounded border border-dashed border-gray-300 p-4 text-sm text-gray-400">
      Unknown block type: {{ block.block_type.slug }}
    </div>
  </template>
</template>
