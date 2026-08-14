// Native IntersectionObserver — no VueUse in this project. Attach the returned
// ref to a sentinel element at the bottom of a list; `callback` fires once
// when it scrolls near-into view. `rootMargin` starts the fetch a bit before
// the sentinel is actually visible, so loading feels continuous rather than
// "hit bottom, wait, then load".
export function useInfiniteScrollSentinel(callback: () => void) {
  const sentinel = ref<HTMLElement | null>(null)
  let observer: IntersectionObserver | null = null

  function attach(el: HTMLElement | null) {
    observer?.disconnect()
    observer = null
    if (el) {
      observer = new IntersectionObserver(
        (entries) => {
          if (entries[0]?.isIntersecting) callback()
        },
        { rootMargin: '200px' },
      )
      observer.observe(el)
    }
  }

  watch(sentinel, attach)
  onUnmounted(() => observer?.disconnect())

  return sentinel
}
