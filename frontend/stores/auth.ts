import { defineStore } from 'pinia'

interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  avatar: string | null
  locale_preference: 'en' | 'km'
  theme_preference: 'light' | 'dark'
  is_2fa_enabled: boolean
  is_superuser: boolean
  is_staff: boolean
}

function apiBase(): string {
  const config = useRuntimeConfig()
  return (import.meta.server ? config.apiBaseInternal : config.public.apiBase) as string
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: null as string | null,
    user: null as User | null,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken),
  },
  actions: {
    /**
     * Silently exchanges the httpOnly refresh cookie for a fresh access token.
     * Access tokens only ever live in memory (Pinia state), so a full page
     * reload/hard navigation loses them — this is what re-establishes the
     * session afterward, without the user having to log in again. Called from
     * plugins/auth.client.ts on every app boot.
     */
    async restoreSession() {
      try {
        const data = await $fetch<{ access: string }>('/api/v1/auth/refresh/', {
          baseURL: apiBase(),
          method: 'POST',
          credentials: 'include',
        })
        this.accessToken = data.access
        this.user = await $fetch<User>('/api/v1/auth/me/', {
          baseURL: apiBase(),
          headers: { Authorization: `Bearer ${data.access}` },
        })
      } catch {
        // no valid refresh cookie — the user simply isn't logged in, not an error
      }
    },
    /**
     * §5.5 — when the account has 2FA enabled, the API returns
     * {requires_2fa, pending_token} instead of a token pair. The caller (the
     * login page) needs to show a code-entry step and call verify2FA() next.
     */
    async login(email: string, password: string) {
      const data = await $fetch<{ access?: string; user?: User; requires_2fa?: boolean; pending_token?: string }>(
        '/api/v1/auth/login/',
        {
          baseURL: apiBase(),
          method: 'POST',
          body: { email, password },
          credentials: 'include',
        },
      )
      if (data.requires_2fa) {
        return { requiresTwoFactor: true as const, pendingToken: data.pending_token as string }
      }
      this.accessToken = data.access as string
      this.user = data.user as User
      return { requiresTwoFactor: false as const }
    },
    async verifyTwoFactor(pendingToken: string, code: string) {
      const data = await $fetch<{ access: string; user: User }>('/api/v1/auth/2fa/verify/', {
        baseURL: apiBase(),
        method: 'POST',
        body: { pending_token: pendingToken, code },
        credentials: 'include',
      })
      this.accessToken = data.access
      this.user = data.user
    },
    async logout() {
      try {
        await $fetch('/api/v1/auth/logout/', {
          baseURL: apiBase(),
          method: 'POST',
          credentials: 'include',
          headers: this.accessToken ? { Authorization: `Bearer ${this.accessToken}` } : {},
        })
      } finally {
        this.accessToken = null
        this.user = null
      }
    },
  },
})
