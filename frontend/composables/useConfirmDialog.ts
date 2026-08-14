interface ConfirmOptions {
  title?: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  danger?: boolean
}

interface ConfirmState extends Required<Omit<ConfirmOptions, 'danger'>> {
  open: boolean
  danger: boolean
}

// Module-scope singleton, not useState: /admin/** is CSR-only (routeRules sets
// ssr: false), so there's no hydration payload to reconcile — a plain ref is
// simpler and avoids the SSR-safety machinery useState exists for.
const state = reactive<ConfirmState>({
  open: false,
  title: 'Are you sure?',
  message: '',
  confirmLabel: 'Confirm',
  cancelLabel: 'Cancel',
  danger: false,
})

let resolver: ((value: boolean) => void) | null = null

/**
 * Promise-based replacement for the browser's native confirm() — every delete
 * action across the admin used confirm(), which is unstyled, blocks the JS
 * thread, and looks nothing like the rest of the app. <ConfirmDialog> (mounted
 * once in layouts/admin.vue) renders `state`; resolve/cancel settle the promise
 * this returns.
 */
export function useConfirmDialog() {
  function confirmAction(options: ConfirmOptions): Promise<boolean> {
    const { t } = useI18n()
    state.title = options.title ?? (options.danger ? t('common.deleteThis') : t('common.areYouSure'))
    state.message = options.message
    state.confirmLabel = options.confirmLabel ?? (options.danger ? t('common.delete') : t('common.confirm'))
    state.cancelLabel = options.cancelLabel ?? t('common.cancel')
    state.danger = options.danger ?? false
    state.open = true
    return new Promise<boolean>((resolve) => {
      resolver = resolve
    })
  }

  function resolve(value: boolean) {
    state.open = false
    resolver?.(value)
    resolver = null
  }

  return { confirmState: state, confirm: confirmAction, resolve }
}
