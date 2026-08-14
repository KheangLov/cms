export async function useAuthFetch<T>(path: string, options: Record<string, any> = {}): Promise<T> {
  const auth = useAuthStore()
  const config = useRuntimeConfig()
  const apiBase = (import.meta.server ? config.apiBaseInternal : config.public.apiBase) as string

  const doFetch = () =>
    $fetch<T>(path, {
      baseURL: apiBase,
      credentials: 'include',
      ...options,
      headers: {
        ...(auth.accessToken ? { Authorization: `Bearer ${auth.accessToken}` } : {}),
        ...(options.headers || {}),
      },
    })

  try {
    return await doFetch()
  } catch (err: any) {
    if (err?.response?.status !== 401 || !auth.accessToken) throw err
    // The access token is short-lived (15 min) — anyone leaving an admin tab
    // open past that had every subsequent write fail with a bare 401 and no
    // visible error, since nothing here ever surfaced it. restoreSession()
    // silently exchanges the httpOnly refresh cookie for a new access token
    // (the same call app boot uses); if the refresh cookie has *also* expired
    // it leaves auth.accessToken untouched, so this retry just fails the same
    // way once more and that final error propagates normally.
    await auth.restoreSession()
    return doFetch()
  }
}
