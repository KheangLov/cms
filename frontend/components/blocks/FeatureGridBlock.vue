<script setup lang="ts">
interface GridItem {
  icon?: string
  label: string | Record<string, string>
  url?: string
}

interface Props {
  block: { props: Record<string, any> }
  locale?: string
}
const props = defineProps<Props>()

function t(field: string): string {
  const value = props.block.props[field]
  if (value && typeof value === 'object') {
    return value[props.locale || 'en'] ?? value.en ?? ''
  }
  return value ?? ''
}

function labelFor(item: GridItem): string {
  if (item.label && typeof item.label === 'object') {
    return item.label[props.locale || 'en'] ?? item.label.en ?? ''
  }
  return item.label ?? ''
}

const items = computed<GridItem[]>(() => (Array.isArray(props.block.props.items) ? props.block.props.items : []))
</script>

<template>
  <section class="mx-auto max-w-6xl px-6 py-10">
    <h2 v-if="t('heading')" class="mb-6 text-2xl font-black">{{ t('heading') }}</h2>
    <div class="feature-grid">
      <NuxtLink
        v-for="(item, i) in items"
        :key="i"
        :to="item.url || '#'"
        class="bento-tile items-center gap-2 text-center"
      >
        <span
          class="flex h-12 w-12 items-center justify-center self-center rounded-full"
          style="background: var(--tonal-bg); color: var(--ember-text)"
        >
          <Icon :name="item.icon || 'solar:widget-5-bold-duotone'" size="1.4rem" />
        </span>
        <span class="text-sm font-semibold">{{ labelFor(item) }}</span>
      </NuxtLink>
    </div>
  </section>
</template>

<style scoped>
.feature-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}
@media (max-width: 900px) {
  .feature-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
