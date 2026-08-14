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
    class="mx-auto flex max-w-6xl flex-col items-center gap-4 px-6 py-8 text-center sm:flex-row sm:justify-between sm:text-left"
    style="background: var(--error-bg); color: var(--error); border-radius: var(--radius-lg); box-shadow: var(--shadow-bento)"
  >
    <div>
      <h2 v-if="t('heading')" class="text-xl font-black">{{ t('heading') }}</h2>
      <p v-if="t('subheading')" class="mt-1 text-sm opacity-90">{{ t('subheading') }}</p>
      <div class="mt-2 flex flex-wrap justify-center gap-4 sm:justify-start">
        <a v-if="block.props.phone" :href="`tel:${block.props.phone}`" class="flex items-center gap-1.5 text-lg font-bold no-underline" style="color: inherit">
          <Icon name="solar:phone-calling-bold-duotone" size="1.1rem" />
          {{ block.props.phone }}
        </a>
        <a v-if="block.props.phoneSecondary" :href="`tel:${block.props.phoneSecondary}`" class="flex items-center gap-1.5 text-lg font-bold no-underline" style="color: inherit">
          <Icon name="solar:phone-calling-bold-duotone" size="1.1rem" />
          {{ block.props.phoneSecondary }}
        </a>
      </div>
    </div>
    <a
      v-if="t('ctaLabel') && block.props.ctaUrl"
      :href="block.props.ctaUrl"
      class="shrink-0 rounded-full px-6 py-3 text-sm font-bold no-underline"
      style="background: var(--error); color: white"
    >
      {{ t('ctaLabel') }}
    </a>
  </section>
</template>
