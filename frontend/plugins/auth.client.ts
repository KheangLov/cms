export default defineNuxtPlugin(async () => {
  const auth = useAuthStore()
  if (!auth.accessToken) {
    await auth.restoreSession()
  }
})
