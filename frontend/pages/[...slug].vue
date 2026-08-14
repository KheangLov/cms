<script setup lang="ts">
const route = useRoute()
const path = Array.isArray(route.params.slug) ? route.params.slug.join('/') : String(route.params.slug || '')
</script>

<template>
  <ResolvedContent :path="path" />
</template>
