<script setup lang="ts">
const colorMode = useColorMode()
const theme = useTheme()

watch(
  () => colorMode.value,
  (value) => {
    theme.change(value === 'dark' ? 'emberDark' : 'emberLight')
  },
  { immediate: true },
)
</script>

<template>
  <v-app>
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </v-app>
</template>
