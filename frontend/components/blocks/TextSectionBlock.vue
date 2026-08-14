<script setup lang="ts">
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
</script>

<template>
  <section class="mx-auto max-w-2xl px-6 py-10">
    <h3 v-if="t('heading')" class="text-2xl font-bold">{{ t('heading') }}</h3>
    <!-- Body is authored HTML via the admin's rich-text editor (Tiptap) — same
         trust model as any CMS's post content, since only logged-in editors with
         write access can produce it. whitespace-pre-line is kept so older,
         plain-text bodies (written before the rich-text upgrade) still render
         their line breaks correctly, since v-html alone wouldn't interpret them. -->
    <div
      v-if="t('body')"
      class="rich-text-body mt-3 whitespace-pre-line text-[color:var(--text-secondary)]"
      v-html="t('body')"
    />
  </section>
</template>

<style scoped>
.rich-text-body :deep(p) {
  margin: 0 0 0.75rem;
}
.rich-text-body :deep(h2) {
  font-size: 1.35rem;
  font-weight: 800;
  color: var(--text-primary);
  margin: 1.25rem 0 0.5rem;
}
.rich-text-body :deep(h3) {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 1rem 0 0.5rem;
}
.rich-text-body :deep(ul),
.rich-text-body :deep(ol) {
  padding-left: 1.5rem;
  margin: 0 0 0.75rem;
}
.rich-text-body :deep(blockquote) {
  border-left: 0.1875rem solid var(--border);
  padding-left: 1rem;
  margin: 0 0 0.75rem;
}
.rich-text-body :deep(a) {
  color: var(--ember-text);
  text-decoration: underline;
}
</style>
