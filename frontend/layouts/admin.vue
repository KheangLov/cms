<script setup lang="ts">
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const colorMode = useColorMode()
const { locale, setLocale } = useI18n()
const { notifications, connect, disconnect } = useNotifications()

const drawer = ref(true)
const showNotifications = ref(false)
const searchPalette = ref<{ openPalette: () => void } | null>(null)

const { t } = useI18n()

const navSections = computed(() => [
  {
    label: t('nav.content'),
    items: [
      { to: '/admin', label: t('nav.dashboard'), icon: 'solar:widget-2-bold-duotone' },
      { to: '/admin/pages', label: t('nav.pages'), icon: 'solar:document-2-bold-duotone' },
      { to: '/admin/posts', label: t('nav.posts'), icon: 'solar:notes-bold-duotone' },
      { to: '/admin/media', label: t('nav.media'), icon: 'solar:gallery-bold-duotone' },
      { to: '/admin/comments', label: t('nav.comments'), icon: 'solar:chat-round-dots-bold-duotone' },
      { to: '/admin/messages', label: t('nav.messages'), icon: 'solar:letter-bold-duotone' },
      { to: '/admin/quizzes', label: t('nav.quizzes'), icon: 'solar:clipboard-check-bold-duotone' },
      { to: '/admin/surveys', label: t('nav.surveys'), icon: 'solar:clipboard-list-bold-duotone' },
    ],
  },
  {
    label: t('nav.access'),
    items: [
      { to: '/admin/users', label: t('nav.users'), icon: 'solar:users-group-rounded-bold-duotone' },
      { to: '/admin/roles', label: t('nav.roles'), icon: 'solar:shield-user-bold-duotone' },
    ],
  },
  {
    label: t('nav.system'),
    items: [
      { to: '/admin/settings', label: t('nav.settings'), icon: 'solar:settings-bold-duotone' },
      { to: '/admin/ai', label: t('nav.aiTools'), icon: 'solar:magic-stick-3-bold-duotone' },
      { to: '/admin/activity', label: t('nav.activityLog'), icon: 'solar:history-2-bold-duotone' },
    ],
  },
])

function isActive(to: string): boolean {
  return to === '/admin' ? route.path === '/admin' : route.path.startsWith(to)
}

async function doLogout() {
  await auth.logout()
  await router.push('/admin/login')
}

// Persisted immediately (not just applied live) so a logged-in admin's choice
// follows them to their next session/device — mirrors account/profile.vue's
// save flow, just fired from the always-visible topbar toggle instead of a
// settings form. Best-effort: a failed PATCH still leaves the live UI correct,
// it just won't survive to the next login.
function changeLocale(code: 'en' | 'km') {
  setLocale(code)
  if (!auth.user) return
  auth.user.locale_preference = code
  useAuthFetch('/api/v1/auth/me/', { method: 'PATCH', body: { locale_preference: code } }).catch(() => {})
}
function changeTheme(mode: 'light' | 'dark') {
  colorMode.preference = mode
  if (!auth.user) return
  auth.user.theme_preference = mode
  useAuthFetch('/api/v1/auth/me/', { method: 'PATCH', body: { theme_preference: mode } }).catch(() => {})
}

onMounted(connect)
onUnmounted(disconnect)
</script>

<template>
  <div>
    <v-navigation-drawer v-model="drawer" class="admin-drawer" width="248" elevation="0">
      <div class="admin-drawer__panel">
        <div class="px-4 py-5">
          <NuxtLink to="/admin" class="flex items-center gap-2.5 no-underline">
            <EmberLogo size="1.6rem" />
            <span class="text-lg font-black gradient-text">Ember CMS</span>
          </NuxtLink>
        </div>
        <div v-for="section in navSections" :key="section.label" class="px-3 pb-2">
          <p class="admin-nav-label">{{ section.label }}</p>
          <NuxtLink
            v-for="item in section.items"
            :key="item.to"
            :to="item.to"
            class="admin-nav-item"
            :class="{ 'admin-nav-item--active': isActive(item.to) }"
          >
            <Icon :name="item.icon" size="1.15rem" />
            {{ item.label }}
          </NuxtLink>
        </div>
      </div>
    </v-navigation-drawer>

    <v-app-bar class="admin-appbar" elevation="0" height="76">
      <div class="admin-appbar__panel">
        <v-app-bar-nav-icon class="md:hidden" @click="drawer = !drawer">
          <Icon name="solar:hamburger-menu-linear" size="1.35rem" />
        </v-app-bar-nav-icon>
        <v-spacer />

        <button class="bento-icon-btn" :title="t('nav.search')" @click="searchPalette?.openPalette()">
          <Icon name="solar:magnifer-bold-duotone" size="1.2rem" />
        </button>

        <div class="bento-pill-group ml-2">
          <button
            class="bento-pill"
            :class="{ 'bento-pill--active': locale === 'en' }"
            title="English"
            @click="changeLocale('en')"
          >
            EN
          </button>
          <button
            class="bento-pill"
            :class="{ 'bento-pill--active': locale === 'km' }"
            title="ខ្មែរ"
            @click="changeLocale('km')"
          >
            ខ្មែរ
          </button>
        </div>

        <div class="bento-pill-group ml-2">
          <button
            class="bento-pill"
            :class="{ 'bento-pill--active': colorMode.preference === 'light' }"
            title="Light theme"
            @click="changeTheme('light')"
          >
            <Icon name="solar:sun-fog-bold-duotone" size="0.95rem" />
          </button>
          <button
            class="bento-pill"
            :class="{ 'bento-pill--active': colorMode.preference === 'dark' }"
            title="Dark theme"
            @click="changeTheme('dark')"
          >
            <Icon name="solar:moon-fog-bold-duotone" size="0.95rem" />
          </button>
        </div>

        <button class="bento-icon-btn ml-2" :title="t('nav.notifications')" @click="showNotifications = !showNotifications">
          <v-badge :content="notifications.length" :model-value="notifications.length > 0" color="secondary">
            <Icon name="solar:bell-bold-duotone" size="1.2rem" />
          </v-badge>
        </button>

        <v-menu>
          <template #activator="{ props }">
            <v-btn variant="text" v-bind="props" class="normal-case ml-1">
              <img
                v-if="auth.user?.avatar"
                :src="auth.user.avatar"
                alt=""
                class="mr-1.5 h-5 w-5 rounded-full object-cover"
              />
              <Icon v-else name="solar:user-circle-bold-duotone" size="1.2rem" class="mr-1.5" />
              {{ auth.user?.email }}
            </v-btn>
          </template>
          <v-list density="compact">
            <v-list-item to="/admin/account/profile" :title="t('nav.profile')">
              <template #prepend><Icon name="solar:user-circle-bold-duotone" size="1.05rem" class="mr-2" /></template>
            </v-list-item>
            <v-list-item to="/admin/account/security" :title="t('nav.accountSecurity')">
              <template #prepend><Icon name="solar:shield-check-bold-duotone" size="1.05rem" class="mr-2" /></template>
            </v-list-item>
            <v-list-item :title="t('nav.logOut')" @click="doLogout">
              <template #prepend><Icon name="solar:logout-2-bold-duotone" size="1.05rem" class="mr-2" /></template>
            </v-list-item>
          </v-list>
        </v-menu>
      </div>
    </v-app-bar>

    <v-navigation-drawer
      v-if="showNotifications"
      class="admin-notif-drawer"
      location="right"
      temporary
      permanent
      width="336"
      elevation="0"
    >
      <div class="admin-notif-drawer__panel p-4">
        <h2 class="text-sm font-bold uppercase" style="color: var(--text-secondary)">{{ t('nav.notifications') }}</h2>
        <p v-if="!notifications.length" class="mt-3 text-sm" style="color: var(--text-faint)">{{ t('common.nothingYet') }}</p>
        <div v-else class="bento-card mt-3">
          <div v-for="(n, i) in notifications" :key="i" class="bento-row">
            <span class="bento-row__icon"><Icon name="solar:bell-bold-duotone" /></span>
            <span class="bento-row__body text-sm">{{ n.event }}</span>
          </div>
        </div>
      </div>
    </v-navigation-drawer>

    <v-main>
      <v-container v-if="!route.meta.fullBleed" fluid class="py-6 px-6">
        <slot />
      </v-container>
      <slot v-else />
    </v-main>

    <ConfirmDialog />
    <AdminSearchPalette ref="searchPalette" />
  </div>
</template>

<style scoped>
/* Both drawers and the app bar render transparent/edge-to-edge — Vuetify's layout
   engine still reserves their full width/height for offsetting v-main — while the
   actual visual chrome lives on the inner __panel, floating with margin + radius +
   shadow so the shell reads as bento cards instead of flush Material Design surfaces. */
.admin-appbar {
  background: var(--bg) !important;
}
.admin-appbar__panel {
  display: flex;
  align-items: center;
  width: 100%;
  height: calc(100% - 1rem);
  margin: 0.5rem;
  padding: 0 1.1rem;
  background: var(--glass-bg);
  backdrop-filter: blur(1.25rem) saturate(160%);
  -webkit-backdrop-filter: blur(1.25rem) saturate(160%);
  border: 0.0625rem solid var(--glass-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-bento);
}
.admin-drawer {
  background: var(--bg) !important;
  border: none;
}
.admin-drawer__panel {
  display: flex;
  flex-direction: column;
  height: calc(100% - 1.5rem);
  margin: 0.5rem;
  background: var(--surface);
  border: 0.0625rem solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-bento);
  overflow-y: auto;
}
.admin-notif-drawer {
  background: var(--bg) !important;
  border: none;
}
.admin-notif-drawer__panel {
  height: calc(100% - 1.5rem);
  margin: 0.5rem;
  background: var(--surface);
  border: 0.0625rem solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-bento);
  overflow-y: auto;
}
/* Tailwind's preflight is deliberately disabled (see assets/css/tailwind.css), so a
   bare <a> keeps the browser's default underline. Chrome links opt out via their own
   bento and nav-item classes; this covers the plain inline links inside pages.
   Scoped to this layout, so the public site's link styling is untouched. */
.v-main :deep(a) {
  text-decoration: none;
}
.admin-nav-label {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-faint);
  margin: 1rem 0 0.4rem 0.5rem;
}
.admin-nav-item {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.55rem 0.7rem;
  margin-bottom: 0.15rem;
  border-radius: var(--radius-md);
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-decoration: none;
  transition: background 0.15s ease, color 0.15s ease;
}
.admin-nav-item:hover {
  background: var(--surface-2);
  color: var(--text-primary);
}
.admin-nav-item--active {
  background: var(--tonal-bg);
  color: var(--ember-text);
}
</style>
