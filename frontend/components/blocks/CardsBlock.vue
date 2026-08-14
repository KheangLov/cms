<script setup lang="ts">
// `:is="'NuxtLink'"` (a plain string) doesn't resolve NuxtLink — Vue's dynamic
// `:is` needs the actual component object for auto-imported/compiler-provided
// components like NuxtLink, not its name. `#components` is Nuxt's virtual
// module that exposes those for exactly this kind of programmatic use.
import { NuxtLink } from '#components'

interface CardItem {
  title: string | Record<string, string>
  body?: string | Record<string, string>
  imageUrl?: string
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

function fieldOf(value: string | Record<string, string> | undefined): string {
  if (value && typeof value === 'object') {
    return value[props.locale || 'en'] ?? value.en ?? ''
  }
  return value ?? ''
}

const cards = computed<CardItem[]>(() => (Array.isArray(props.block.props.cards) ? props.block.props.cards : []))
</script>

<template>
  <section class="mx-auto max-w-6xl px-6 py-10">
    <h2 v-if="t('heading')" class="mb-6 text-2xl font-black">{{ t('heading') }}</h2>
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <component
        :is="card.url ? NuxtLink : 'div'"
        v-for="(card, i) in cards"
        :key="i"
        :to="card.url"
        class="bento-tile block p-5"
      >
        <img
          v-if="card.imageUrl"
          :src="card.imageUrl"
          alt=""
          class="mb-3 h-16 w-16 rounded-full object-cover"
          style="background: var(--surface-2)"
        />
        <h3 class="font-bold">{{ fieldOf(card.title) }}</h3>
        <p v-if="fieldOf(card.body)" class="mt-2 text-sm" style="color: var(--text-secondary)">
          {{ fieldOf(card.body) }}
        </p>
      </component>
    </div>
  </section>
</template>
