<script setup lang="ts">
interface NavLink {
  label: string | Record<string, string>
  pageId?: number
  url?: string
  resolvedUrl?: string | null
}

interface Props {
  block: { props: Record<string, any> }
  locale?: string
}
const props = defineProps<Props>()

const { locale, setLocale } = useI18n()
const colorMode = useColorMode()
const mobileOpen = ref(false)

// The server has no way to know the visitor's stored theme preference (same
// issue app.vue already works around for Vuetify's own theme sync) — SSR always
// renders as if preference === 'light', so the first client render has to match
// that exactly, then swap to the real preference only after hydration completes.
const mounted = ref(false)
onMounted(() => {
  mounted.value = true
})

function t(field: string): string {
  const value = props.block.props[field]
  if (value && typeof value === 'object') {
    return value[props.locale || 'en'] ?? value.en ?? ''
  }
  return value ?? ''
}

function labelFor(link: NavLink): string {
  if (link.label && typeof link.label === 'object') {
    return link.label[props.locale || 'en'] ?? link.label.en ?? ''
  }
  return link.label ?? ''
}

function hrefFor(link: NavLink): string {
  return link.resolvedUrl || link.url || '#'
}

const links = computed<NavLink[]>(() => (Array.isArray(props.block.props.links) ? props.block.props.links : []))

const searchOpen = ref(false)
const searchQuery = ref('')
const router = useRouter()
function submitSearch() {
  const q = searchQuery.value.trim()
  if (!q) return
  router.push(`/search?q=${encodeURIComponent(q)}`)
  searchOpen.value = false
  searchQuery.value = ''
}

// Pre-hydration guess is always 'light' (SSR can't know the visitor's stored
// preference — same constraint app.vue's own theme sync documents), so the
// active pill only reflects the real value once `mounted` flips true.
function isDark(): boolean {
  return mounted.value && colorMode.preference === 'dark'
}
</script>

<template>
  <header class="sticky top-0 z-40 border-b" style="background: var(--surface); border-color: var(--border)">
    <div class="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-3">
      <NuxtLink to="/" class="flex shrink-0 items-center gap-2 no-underline" style="color: var(--text-primary)">
        <img v-if="block.props.logoUrl" :src="block.props.logoUrl" alt="" class="h-8 w-8 rounded-full object-cover" />
        <span class="text-lg font-black">{{ t('logoText') || 'Site' }}</span>
      </NuxtLink>

      <nav class="hidden flex-1 items-center justify-center gap-6 md:flex">
        <a
          v-for="(link, i) in links"
          :key="i"
          :href="hrefFor(link)"
          class="text-sm font-semibold no-underline"
          style="color: var(--text-secondary)"
        >
          {{ labelFor(link) }}
        </a>
      </nav>

      <div class="hidden shrink-0 items-center gap-2 md:flex">
        <form v-if="searchOpen" class="flex items-center" @submit.prevent="submitSearch">
          <input
            v-model="searchQuery"
            type="search"
            placeholder="Search…"
            autofocus
            class="bento-input"
            style="width: 10rem; height: 2.25rem"
            @blur="!searchQuery && (searchOpen = false)"
          />
        </form>
        <button v-else class="bento-icon-btn" title="Search" @click="searchOpen = true">
          <Icon name="solar:magnifer-bold-duotone" size="1.05rem" />
        </button>
        <div class="bento-pill-group">
          <button class="bento-pill" :class="{ 'bento-pill--active': locale === 'en' }" title="English" @click="setLocale('en')">
            EN
          </button>
          <button class="bento-pill" :class="{ 'bento-pill--active': locale === 'km' }" title="ខ្មែរ" @click="setLocale('km')">
            ខ្មែរ
          </button>
        </div>
        <div class="bento-pill-group">
          <button class="bento-pill" :class="{ 'bento-pill--active': !isDark() }" title="Light theme" @click="colorMode.preference = 'light'">
            <Icon name="solar:sun-fog-bold-duotone" size="0.95rem" />
          </button>
          <button class="bento-pill" :class="{ 'bento-pill--active': isDark() }" title="Dark theme" @click="colorMode.preference = 'dark'">
            <Icon name="solar:moon-fog-bold-duotone" size="0.95rem" />
          </button>
        </div>
      </div>

      <!-- `.bento-icon-btn` in tokens.scss is unlayered CSS; Tailwind's utilities
           live in `layer(utilities)`, and unlayered rules always beat layered ones
           regardless of source order — so `md:hidden` directly on a bento-icon-btn
           element is silently overridden by its own `display: inline-flex`. Putting
           `md:hidden` on a plain wrapper instead sidesteps the conflict entirely. -->
      <div class="md:hidden">
        <button class="bento-icon-btn" title="Menu" @click="mobileOpen = !mobileOpen">
          <Icon :name="mobileOpen ? 'solar:close-circle-bold-duotone' : 'solar:hamburger-menu-linear'" size="1.2rem" />
        </button>
      </div>
    </div>

    <div v-if="mobileOpen" class="border-t px-6 py-4 md:hidden" style="border-color: var(--border)">
      <a
        v-for="(link, i) in links"
        :key="i"
        :href="hrefFor(link)"
        class="block py-2 text-sm font-semibold no-underline"
        style="color: var(--text-secondary)"
      >
        {{ labelFor(link) }}
      </a>
      <form class="mt-3 flex items-center gap-2" @submit.prevent="submitSearch">
        <input v-model="searchQuery" type="search" placeholder="Search…" class="bento-input flex-1" />
        <button type="submit" class="bento-icon-btn" title="Search">
          <Icon name="solar:magnifer-bold-duotone" size="1.05rem" />
        </button>
      </form>
      <div class="mt-2 flex items-center gap-2 border-t pt-3" style="border-color: var(--border)">
        <div class="bento-pill-group">
          <button class="bento-pill" :class="{ 'bento-pill--active': locale === 'en' }" title="English" @click="setLocale('en')">
            EN
          </button>
          <button class="bento-pill" :class="{ 'bento-pill--active': locale === 'km' }" title="ខ្មែរ" @click="setLocale('km')">
            ខ្មែរ
          </button>
        </div>
        <div class="bento-pill-group">
          <button class="bento-pill" :class="{ 'bento-pill--active': !isDark() }" title="Light theme" @click="colorMode.preference = 'light'">
            <Icon name="solar:sun-fog-bold-duotone" size="0.95rem" />
          </button>
          <button class="bento-pill" :class="{ 'bento-pill--active': isDark() }" title="Dark theme" @click="colorMode.preference = 'dark'">
            <Icon name="solar:moon-fog-bold-duotone" size="0.95rem" />
          </button>
        </div>
      </div>
    </div>
  </header>
</template>
