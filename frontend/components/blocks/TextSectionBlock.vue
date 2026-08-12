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
  <section class="mx-auto max-w-2xl px-6 py-10">
    <h3 v-if="t('heading')" class="text-2xl font-bold">{{ t('heading') }}</h3>
    <p v-if="t('body')" class="mt-3 whitespace-pre-line text-[color:var(--text-secondary)]">
      {{ t('body') }}
    </p>
  </section>
</template>
