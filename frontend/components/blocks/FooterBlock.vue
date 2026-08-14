<script setup lang="ts">
interface NavLink {
  label: string | Record<string, string>
  pageId?: number
  url?: string
  resolvedUrl?: string | null
}
interface FooterColumn {
  heading: string | Record<string, string>
  links: NavLink[]
}
interface SocialLink {
  icon?: string
  label?: string
  url: string
}

interface Props {
  block: { props: Record<string, any> }
  locale?: string
}
const props = defineProps<Props>()

function t(field: string): string {
  const value = props.block.props[field]
  if (value && typeof value === 'object') {
    return value[props.locale || 'en'] ?? value.en ?? ''
  }
  return value ?? ''
}

function fieldOf(value: string | Record<string, string> | undefined): string {
  if (value && typeof value === 'object') {
    return value[props.locale || 'en'] ?? value.en ?? ''
  }
  return value ?? ''
}

function hrefFor(link: NavLink): string {
  return link.resolvedUrl || link.url || '#'
}

// Footer used to be a single flat `links` list before it grew multi-column
// support — older content (or a block that hasn't been re-saved yet) still has
// that shape, so it's wrapped into one unnamed column rather than dropped.
const columns = computed<FooterColumn[]>(() => {
  if (Array.isArray(props.block.props.columns) && props.block.props.columns.length) {
    return props.block.props.columns
  }
  if (Array.isArray(props.block.props.links) && props.block.props.links.length) {
    return [{ heading: '', links: props.block.props.links }]
  }
  return []
})

const socialLinks = computed<SocialLink[]>(() =>
  Array.isArray(props.block.props.socialLinks) ? props.block.props.socialLinks : [],
)

const { t: $t } = useI18n()
const year = new Date().getFullYear()
</script>

<template>
  <footer class="border-t" style="background: var(--surface-2); border-color: var(--border)">
    <div class="mx-auto max-w-6xl px-6 py-10">
      <div class="flex flex-wrap items-start gap-8">
        <div class="min-w-[10rem] flex-1">
          <NuxtLink to="/" class="flex items-center gap-2 no-underline" style="color: var(--text-primary)">
            <img v-if="block.props.logoUrl" :src="block.props.logoUrl" alt="" class="h-8 w-8 rounded-full object-cover" />
            <span v-if="t('logoText')" class="text-lg font-black">{{ t('logoText') }}</span>
          </NuxtLink>
          <div class="mt-3 text-sm" style="color: var(--text-secondary)">
            <p v-if="block.props.contactEmail">{{ block.props.contactEmail }}</p>
            <p v-if="block.props.contactPhone" class="mt-1">{{ block.props.contactPhone }}</p>
            <p v-if="block.props.contactAddress" class="mt-1 whitespace-pre-line">{{ block.props.contactAddress }}</p>
          </div>
          <div v-if="socialLinks.length" class="mt-4 flex gap-2">
            <a
              v-for="(social, i) in socialLinks"
              :key="i"
              :href="social.url"
              :aria-label="social.label || $t('publicFooter.socialLink')"
              class="bento-icon-btn"
              target="_blank"
              rel="noopener"
            >
              <Icon :name="social.icon || 'solar:link-circle-bold-duotone'" size="1.05rem" />
            </a>
          </div>
        </div>

        <div v-for="(column, c) in columns" :key="c" class="min-w-[8rem]">
          <h3 v-if="fieldOf(column.heading)" class="text-xs font-bold uppercase" style="color: var(--text-faint)">
            {{ fieldOf(column.heading) }}
          </h3>
          <nav class="mt-2 flex flex-col gap-2">
            <a
              v-for="(link, i) in column.links"
              :key="i"
              :href="hrefFor(link)"
              class="text-sm font-semibold no-underline"
              style="color: var(--text-secondary)"
            >
              {{ fieldOf(link.label) }}
            </a>
          </nav>
        </div>
      </div>

      <div class="mt-8 border-t pt-6 text-sm" style="border-color: var(--border); color: var(--text-faint)">
        {{ t('copyrightText') || `© ${year}` }}
      </div>
    </div>
  </footer>
</template>
