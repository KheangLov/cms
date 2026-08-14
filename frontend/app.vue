<script setup lang="ts">
const colorMode = useColorMode()
const theme = useTheme()
const auth = useAuthStore()
const { locale, setLocale } = useI18n()

// tokens.scss keys the Kantumruy Pro font-family swap off :lang(km) — without
// this, <html lang> stays empty forever, that selector never matches, and
// Khmer text silently falls back to whatever Khmer glyphs the OS ships.
useHead({ htmlAttrs: { lang: locale } })

// @nuxtjs/i18n's own cookie-based restoration runs during SSR request
// handling — it never fires for /admin/** (routeRules sets ssr: false there),
// so a returning admin visitor's saved language silently reset to the
// default on every load. This client-side read is the CSR-route fallback;
// it's a no-op on SSR pages where the cookie already won.
onMounted(() => {
  const saved = useCookie('ember_locale').value as string | undefined
  if (saved && saved !== locale.value) setLocale(saved)
})

function syncTheme(value: string) {
  theme.change(value === 'dark' ? 'emberDark' : 'emberLight')
}

// Deliberately not `{ immediate: true }`. The server has no way to know the
// visitor's system colour preference, so SSR always renders v-theme--emberLight.
// Running the sync during setup switched Vuetify to emberDark *before* Vue
// compared the markup, so every public page load in dark mode logged a hydration
// class mismatch on <v-application>. Syncing on mount lets hydration compare like
// for like; @nuxtjs/color-mode's own pre-paint script has already set the `.dark`
// class on <html>, which is what the tokens in assets/css/tokens.scss key off, so
// there's no visible flash while Vuetify catches up a tick later.
watch(() => colorMode.value, syncTheme)
onMounted(() => syncTheme(colorMode.value))

// A logged-in user's saved locale_preference/theme_preference win over
// whatever the anonymous-visit cookie/guess had — this fires for every path
// that populates auth.user (login, 2FA verify, social callback, and session
// restore on a fresh browser/device), so signing in restores their choice
// instead of leaving it stuck at the cookie's guess.
watch(
  () => auth.user,
  (user) => {
    if (!user) return
    if (user.locale_preference && user.locale_preference !== locale.value) {
      locale.value = user.locale_preference
    }
    if (user.theme_preference && user.theme_preference !== colorMode.preference) {
      colorMode.preference = user.theme_preference
    }
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
