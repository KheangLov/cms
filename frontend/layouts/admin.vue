<script setup lang="ts">
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const colorMode = useColorMode()
const { notifications, connect, disconnect } = useNotifications()

const drawer = ref(true)
const showNotifications = ref(false)

const navSections = [
  {
    label: 'Content',
    items: [
      { to: '/admin', label: 'Dashboard', icon: 'M4 4h7v7H4V4Zm9 0h7v4h-7V4Zm0 6h7v10h-7V10ZM4 13h7v7H4v-7Z' },
      { to: '/admin/pages', label: 'Pages', icon: 'M6 2h9l5 5v15H6V2Zm8 1.5V8h4.5' },
      { to: '/admin/posts', label: 'Posts', icon: 'M4 4h16v4H4V4Zm0 6h16v2H4v-2Zm0 5h16v2H4v-2Zm0 5h10v2H4v-2Z' },
      { to: '/admin/media', label: 'Media', icon: 'M4 4h16v16H4V4Zm3 12 3.5-4.5L13 15l3-4 3 5H7Z' },
      { to: '/admin/comments', label: 'Comments', icon: 'M4 4h16v12H8l-4 4V4Z' },
    ],
  },
  {
    label: 'Access',
    items: [
      { to: '/admin/users', label: 'Users', icon: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm0 2c-4 0-8 2-8 5v1h16v-1c0-3-4-5-8-5Z' },
      { to: '/admin/roles', label: 'Roles', icon: 'M12 2 4 5v6c0 5 3.5 9 8 11 4.5-2 8-6 8-11V5l-8-3Z' },
    ],
  },
  {
    label: 'System',
    items: [
      { to: '/admin/settings', label: 'Settings', icon: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Zm8.4 4a7.9 7.9 0 0 0-.15-1.5l2.1-1.6-2-3.5-2.5 1a8 8 0 0 0-2.6-1.5L14.8 2H9.2l-.45 2.9a8 8 0 0 0-2.6 1.5l-2.5-1-2 3.5 2.1 1.6a7.9 7.9 0 0 0 0 3l-2.1 1.6 2 3.5 2.5-1a8 8 0 0 0 2.6 1.5l.45 2.9h5.6l.45-2.9a8 8 0 0 0 2.6-1.5l2.5 1 2-3.5-2.1-1.6c.1-.5.15-1 .15-1.5Z' },
      { to: '/admin/ai', label: 'AI Tools', icon: 'M12 2 2 7l10 5 10-5-10-5Zm0 20-10-5v-6l10 5 10-5v6l-10 5Z' },
      { to: '/admin/activity', label: 'Activity Log', icon: 'M4 4h16v2H4V4Zm0 14h10v2H4v-2Zm0-7h16v2H4v-2Z' },
    ],
  },
]

function isActive(to: string): boolean {
  return to === '/admin' ? route.path === '/admin' : route.path.startsWith(to)
}

async function doLogout() {
  await auth.logout()
  await router.push('/admin/login')
}

const cycleTheme = () => {
  const order = ['system', 'light', 'dark']
  const next = order[(order.indexOf(colorMode.preference) + 1) % order.length]
  colorMode.preference = next
}

onMounted(connect)
onUnmounted(disconnect)
</script>

<template>
  <div>
    <v-navigation-drawer v-model="drawer" class="admin-drawer" width="232">
      <div class="px-4 py-5">
        <NuxtLink to="/admin" class="text-lg font-black gradient-text">Ember CMS</NuxtLink>
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
          <svg width="18" height="18" viewBox="0 0 24 24"><path :d="item.icon" fill="currentColor" /></svg>
          {{ item.label }}
        </NuxtLink>
      </div>
    </v-navigation-drawer>

    <v-app-bar class="admin-appbar" elevation="0">
      <v-app-bar-nav-icon class="md:hidden" @click="drawer = !drawer" />
      <v-spacer />

      <v-btn variant="text" size="small" @click="cycleTheme">
        {{ colorMode.preference === 'system' ? 'System' : colorMode.preference === 'dark' ? 'Dark' : 'Light' }}
      </v-btn>

      <v-btn variant="text" icon size="small" @click="showNotifications = !showNotifications">
        <v-badge :content="notifications.length" :model-value="notifications.length > 0" color="secondary">
          <svg width="20" height="20" viewBox="0 0 24 24">
            <path
              d="M12 22a2.5 2.5 0 0 0 2.45-2h-4.9A2.5 2.5 0 0 0 12 22Zm7-6v-5a7 7 0 0 0-5.5-6.84V3a1.5 1.5 0 0 0-3 0v1.16A7 7 0 0 0 5 11v5l-2 2v1h18v-1l-2-2Z"
              fill="currentColor"
            />
          </svg>
        </v-badge>
      </v-btn>

      <v-menu>
        <template #activator="{ props }">
          <v-btn variant="text" v-bind="props" class="normal-case">
            {{ auth.user?.email }}
          </v-btn>
        </template>
        <v-list density="compact">
          <v-list-item to="/admin/account/security" title="Account & security" />
          <v-list-item title="Log out" @click="doLogout" />
        </v-list>
      </v-menu>
    </v-app-bar>

    <v-navigation-drawer v-if="showNotifications" location="right" temporary permanent width="320">
      <div class="p-4">
        <h2 class="text-sm font-bold uppercase text-secondary">Notifications</h2>
        <p v-if="!notifications.length" class="mt-3 text-sm" style="color: var(--text-faint)">Nothing yet.</p>
        <ul class="mt-3 space-y-2">
          <li v-for="(n, i) in notifications" :key="i" class="admin-notification">
            {{ n.event }}
          </li>
        </ul>
      </div>
    </v-navigation-drawer>

    <v-main>
      <v-container v-if="!route.meta.fullBleed" fluid class="py-6 px-6">
        <slot />
      </v-container>
      <slot v-else />
    </v-main>
  </div>
</template>

<style scoped>
.admin-appbar {
  background: var(--glass-bg) !important;
  backdrop-filter: blur(1.25rem) saturate(160%);
  -webkit-backdrop-filter: blur(1.25rem) saturate(160%);
  border-bottom: 0.0625rem solid var(--glass-border);
}
.admin-drawer {
  background: var(--surface) !important;
  border-right: 0.0625rem solid var(--border) !important;
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
  gap: 0.6rem;
  padding: 0.5rem 0.6rem;
  border-radius: var(--radius-sm);
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-decoration: none;
}
.admin-nav-item:hover {
  background: var(--surface-2);
}
.admin-nav-item--active {
  background: var(--tonal-bg);
  color: var(--ember-text);
}
.admin-notification {
  font-size: 0.82rem;
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  padding: 0.5rem 0.7rem;
}
</style>
