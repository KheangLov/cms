export function useAuthFetch<T>(path: string, options: Record<string, any> = {}): Promise<T> {
  const auth = useAuthStore()
  const config = useRuntimeConfig()
  const apiBase = (import.meta.server ? config.apiBaseInternal : config.public.apiBase) as string

  return $fetch<T>(path, {
    baseURL: apiBase,
    credentials: 'include',
    ...options,
    headers: {
      ...(auth.accessToken ? { Authorization: `Bearer ${auth.accessToken}` } : {}),
      ...(options.headers || {}),
    },
  })
}
