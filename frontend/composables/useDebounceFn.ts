import { debounce } from 'lodash-es'

/** Thin wrapper so every list page's search box debounces the same way,
 * without each one pulling lodash-es directly. */
export function useDebounceFn<T extends (...args: any[]) => any>(fn: T, waitMs = 300) {
  return debounce(fn, waitMs)
}
