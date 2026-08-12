<script setup lang="ts">
// Rendered client-side only — see routeRules in nuxt.config.ts (§6.3). This is a
// placeholder; the real admin shell (app bar, nav rail, auth guard) lands in Phase 1.
useSeoMeta({ title: 'Admin — CMS Platform' })
</script>

<template>
  <div>
    <v-app-bar color="surface" elevation="0">
      <v-app-bar-title>Ember CMS — Admin</v-app-bar-title>
    </v-app-bar>
    <v-main>
      <v-container class="py-8">
        <v-alert type="info" variant="tonal" color="primary">
          Admin shell placeholder — rendered client-side (CSR), not SSR. Real dashboard
          (auth, nav rail, dashboard cards) arrives in Phase 1–2.
        </v-alert>
      </v-container>
    </v-main>
  </div>
</template>
