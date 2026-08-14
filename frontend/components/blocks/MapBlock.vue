<script setup lang="ts">
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
</script>

<template>
  <section class="mx-auto max-w-6xl px-6 py-10">
    <h2 v-if="t('heading')" class="mb-4 text-2xl font-black">{{ t('heading') }}</h2>
    <div v-if="block.props.embedUrl" class="overflow-hidden" style="border-radius: var(--radius-lg); box-shadow: var(--shadow-bento)">
      <iframe
        :src="block.props.embedUrl"
        class="h-96 w-full border-0"
        loading="lazy"
        referrerpolicy="no-referrer-when-downgrade"
      />
    </div>
  </section>
</template>
