<script setup lang="ts">
const colorMode = useColorMode()
const theme = useTheme()

watch(
  () => colorMode.value,
  (value) => {
    theme.global.name.value = value === 'dark' ? 'emberDark' : 'emberLight'
  },
  { immediate: true },
)
</script>

<template>
  <v-app>
    <NuxtPage />
  </v-app>
</template>
