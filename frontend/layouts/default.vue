<script setup lang="ts">
// Site-wide chrome (Navbar/Footer), fetched once per layout mount rather than
// per page — every route using this layout (i.e. everything except /admin/**)
// gets the same nav/footer without a page author re-adding it. See
// backend/apps/pages/resolver.py::SiteChromeView.
const config = useRuntimeConfig()
const apiBase = (import.meta.server ? config.apiBaseInternal : config.public.apiBase) as string
const { locale } = useI18n()

const { data } = await useFetch<{ blocks: any[] }>('/api/v1/site-chrome/', {
  key: 'site-chrome',
  baseURL: apiBase,
})

const blocks = computed(() => data.value?.blocks || [])
const navbarBlock = computed(() => blocks.value.find((b) => b.block_type.slug === 'navbar'))
const footerBlock = computed(() => blocks.value.find((b) => b.block_type.slug === 'footer'))
</script>

<template>
  <div class="flex min-h-screen flex-col">
    <BlocksNavbarBlock v-if="navbarBlock" :block="navbarBlock" :locale="locale" />
    <div class="flex-1">
      <slot />
    </div>
    <BlocksFooterBlock v-if="footerBlock" :block="footerBlock" :locale="locale" />
  </div>
</template>
