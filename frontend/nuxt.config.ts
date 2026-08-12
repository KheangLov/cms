import tailwindcss from '@tailwindcss/vite'

// See CMS_BUILD_PROMPT.md §2, §6.3, §11 for the reasoning behind every section below.
export default defineNuxtConfig({
  compatibilityDate: '2026-08-12',
  devtools: { enabled: true },

  modules: [
    'vuetify-nuxt-module',
    '@pinia/nuxt',
    '@nuxtjs/i18n',
    '@nuxtjs/color-mode',
    '@nuxt/image',
  ],

  css: ['~/assets/css/tokens.scss', '~/assets/css/tailwind.css'],

  vite: {
    plugins: [tailwindcss()],
  },

  // Hybrid rendering — CMS_BUILD_PROMPT.md §6.3: public pages stay SSR (good SEO,
  // fast first paint); the admin dashboard is a pure client-rendered SPA behind auth,
  // since it's never indexed and SSR would just add server load for no benefit.
  routeRules: {
    '/admin/**': { ssr: false, robots: false },
  },

  runtimeConfig: {
    // Server-only — SSR runs inside the frontend container and must reach the backend
    // container via the Docker network's service name, not "localhost". §6.3.
    apiBaseInternal: process.env.NUXT_API_BASE_INTERNAL || 'http://backend:8000',
    public: {
      // Client-facing — the browser reaches the backend via its published host port.
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000',
    },
  },

  colorMode: {
    // §11.8 — three states: system (default), explicit light, explicit dark.
    preference: 'system',
    fallback: 'light',
    classSuffix: '',
  },

  i18n: {
    locales: [
      { code: 'en', language: 'en-US', name: 'English' },
      { code: 'km', language: 'km-KH', name: 'ខ្មែរ' },
    ],
    defaultLocale: 'en',
    strategy: 'prefix_except_default',
  },

  vuetify: {
    moduleOptions: {},
    vuetifyOptions: {
      theme: {
        defaultTheme: 'emberLight',
        themes: {
          // Ember palette — CMS_BUILD_PROMPT.md §11.1, §11.7.
          emberLight: {
            dark: false,
            colors: {
              primary: '#FF6B4A',
              secondary: '#B0296B',
              tertiary: '#E3B23C',
              background: '#FBF7F2',
              surface: '#FFFFFF',
              error: '#D93636',
              success: '#2F9D68',
              info: '#3873D9',
              warning: '#E3B23C',
            },
          },
          emberDark: {
            dark: true,
            colors: {
              primary: '#FF7C5C',
              secondary: '#E24F92',
              tertiary: '#F0C15A',
              background: '#14111C',
              surface: '#1E1A27',
              error: '#F2695D',
              success: '#4FCB8E',
              info: '#6FA6F2',
              warning: '#F0C15A',
            },
          },
        },
      },
    },
  },

  typescript: {
    strict: true,
  },
})
