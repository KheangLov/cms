export interface NotificationEvent {
  event: string
  [key: string]: unknown
}

/**
 * CMS_BUILD_PROMPT.md §5.15 — comment/AI/media events pushed over Channels.
 * The token goes in the query string, not an Authorization header: the native
 * WebSocket API can't attach custom headers to the handshake request. See
 * apps/realtime/middleware.py on the backend for the matching auth.
 */
export function useNotifications() {
  const notifications = ref<NotificationEvent[]>([])
  const auth = useAuthStore()
  const config = useRuntimeConfig()
  let socket: WebSocket | null = null

  function connect() {
    if (!auth.accessToken || socket) return
    const wsBase = (config.public.apiBase as string).replace(/^http/, 'ws')
    socket = new WebSocket(`${wsBase}/ws/notifications/?token=${auth.accessToken}`)
    socket.onmessage = (msg) => {
      try {
        notifications.value.unshift(JSON.parse(msg.data))
      } catch {
        // ignore malformed frames
      }
    }
    socket.onclose = () => {
      socket = null
    }
  }

  function disconnect() {
    socket?.close()
    socket = null
  }

  return { notifications, connect, disconnect }
}
