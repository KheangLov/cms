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
  <section
    class="relative flex min-h-[20rem] flex-col items-center justify-center rounded-lg px-6 py-16 text-center text-white"
    :style="
      block.props.backgroundImageUrl
        ? {
            backgroundImage: `url(${block.props.backgroundImageUrl})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
          }
        : { background: 'var(--gradient-primary)' }
    "
  >
    <h2 v-if="t('heading')" class="text-4xl font-black">{{ t('heading') }}</h2>
    <p v-if="t('subheading')" class="mt-2 text-lg opacity-90">{{ t('subheading') }}</p>
    <a
      v-if="t('ctaLabel') && block.props.ctaUrl"
      :href="block.props.ctaUrl"
      class="mt-6 inline-block rounded-full bg-white px-6 py-3 font-bold text-black"
    >
      {{ t('ctaLabel') }}
    </a>
  </section>
</template>
