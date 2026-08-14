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
  <div class="cols-block grid gap-4 px-6 py-4" :style="{ '--col-count': block.props.columnCount || 2 }">
    <BlocksBlockRenderer :blocks="block.children" :locale="locale" />
  </div>
</template>

<style scoped>
.cols-block {
  grid-template-columns: repeat(var(--col-count), minmax(0, 1fr));
}
/* A fixed N-column grid stops being usable well before mobile width — collapse
   to a single column rather than squeezing every column illegibly narrow. */
@media (max-width: 640px) {
  .cols-block {
    grid-template-columns: 1fr;
  }
}
</style>
