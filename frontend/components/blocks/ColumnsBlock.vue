<script setup lang="ts">
interface BlockNode {
  id: number
  block_type: { slug: string; name: string }
  order: number
  props: Record<string, any>
  children: BlockNode[]
}

defineProps<{
  block: { props: Record<string, any>; children: BlockNode[] }
  locale?: string
}>()
</script>

<template>
  <!-- BlocksBlockRenderer resolves via Nuxt's global component auto-import (no JS
       import here) — avoids a circular import with BlockRenderer.vue, which imports
       this component to dispatch on block_type.slug. -->
  <div
    class="grid gap-4 px-6 py-4"
    :style="{ gridTemplateColumns: `repeat(${block.props.columnCount || 2}, minmax(0, 1fr))` }"
  >
    <BlocksBlockRenderer :blocks="block.children" :locale="locale" />
  </div>
</template>
