<script setup lang="ts">
// Ember CMS logomark — an asymmetric bento grid, so the identity is the same shape
// language as the dashboard it sits on. Four tiles: one tall ember→wine gradient tile
// carrying the brand gradient, a gold accent square, and two muted tiles.
//
// Sized in em so it scales with whatever font-size the caller sets, and the gradient
// id is per-instance (useId) — two logos on one page with a shared id would make the
// second one reference the first one's def.
withDefaults(defineProps<{ size?: string }>(), { size: '1.75rem' })

const gradientId = `ember-logo-gradient-${useId()}`
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 32 32"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    role="img"
    aria-label="Ember CMS"
  >
    <defs>
      <linearGradient :id="gradientId" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#FF6B4A" />
        <stop offset="100%" stop-color="#B0296B" />
      </linearGradient>
    </defs>

    <!-- Tall gradient tile — the "ember" -->
    <rect x="1" y="1" width="13" height="30" rx="5" :fill="`url(#${gradientId})`" />
    <!-- Gold accent -->
    <rect x="17" y="1" width="14" height="13" rx="5" fill="#E3B23C" />
    <!-- Two muted tiles, tinted from the ember so they read as one family -->
    <rect x="17" y="17" width="6.5" height="14" rx="3" fill="#FF6B4A" fill-opacity="0.55" />
    <rect x="26" y="17" width="5" height="14" rx="2.5" fill="#B0296B" fill-opacity="0.4" />
  </svg>
</template>
