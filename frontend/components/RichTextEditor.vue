<script setup lang="ts">
import Link from '@tiptap/extension-link'
import StarterKit from '@tiptap/starter-kit'
import { EditorContent, useEditor } from '@tiptap/vue-3'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()
const { t } = useI18n()

const editor = useEditor({
  content: props.modelValue,
  extensions: [StarterKit, Link.configure({ openOnClick: false })],
  editorProps: {
    attributes: { class: 'rich-text-editor__content' },
  },
  onUpdate: ({ editor: e }) => {
    emit('update:modelValue', e.getHTML())
  },
})

// The block-props panel swaps `selectedBlock` when a different block is
// clicked, but Tiptap's own editor instance doesn't reset itself — without
// this the toolbar would silently keep editing the *previous* block's content.
watch(
  () => props.modelValue,
  (value) => {
    if (editor.value && value !== editor.value.getHTML()) {
      editor.value.commands.setContent(value || '', { emitUpdate: false })
    }
  },
)

onBeforeUnmount(() => {
  editor.value?.destroy()
})

function toggle(command: string) {
  if (!editor.value) return
  const chain = editor.value.chain().focus() as any
  chain[command]().run()
}

function setLink() {
  if (!editor.value) return
  const previous = editor.value.getAttributes('link').href
  const url = window.prompt(t('richTextEditor.linkUrlPrompt'), previous || 'https://')
  if (url === null) return
  const chain = editor.value.chain().focus() as any
  if (url === '') {
    chain.unsetLink().run()
  } else {
    chain.setLink({ href: url }).run()
  }
}
</script>

<template>
  <div class="rich-text-editor">
    <div v-if="editor" class="rich-text-editor__toolbar">
      <button type="button" :class="{ active: editor.isActive('bold') }" :title="$t('richTextEditor.bold')" @click="toggle('toggleBold')">
        <Icon name="solar:text-bold-square-bold-duotone" size="1rem" />
      </button>
      <button type="button" :class="{ active: editor.isActive('italic') }" :title="$t('richTextEditor.italic')" @click="toggle('toggleItalic')">
        <Icon name="solar:text-italic-square-bold-duotone" size="1rem" />
      </button>
      <span class="rich-text-editor__divider" />
      <button type="button" :class="{ active: editor.isActive('heading', { level: 2 }) }" :title="$t('richTextEditor.heading2')" @click="editor.chain().focus().toggleHeading({ level: 2 }).run()">
        H2
      </button>
      <button type="button" :class="{ active: editor.isActive('heading', { level: 3 }) }" :title="$t('richTextEditor.heading3')" @click="editor.chain().focus().toggleHeading({ level: 3 }).run()">
        H3
      </button>
      <span class="rich-text-editor__divider" />
      <button type="button" :class="{ active: editor.isActive('bulletList') }" :title="$t('richTextEditor.bulletList')" @click="toggle('toggleBulletList')">
        <Icon name="solar:list-bold-duotone" size="1rem" />
      </button>
      <button type="button" :class="{ active: editor.isActive('orderedList') }" :title="$t('richTextEditor.numberedList')" @click="toggle('toggleOrderedList')">
        <Icon name="solar:sort-by-alphabet-bold-duotone" size="1rem" />
      </button>
      <button type="button" :class="{ active: editor.isActive('blockquote') }" :title="$t('richTextEditor.quote')" @click="toggle('toggleBlockquote')">
        <Icon name="solar:document-text-bold-duotone" size="1rem" />
      </button>
      <span class="rich-text-editor__divider" />
      <button type="button" :class="{ active: editor.isActive('link') }" :title="$t('richTextEditor.link')" @click="setLink">
        <Icon name="solar:link-bold-duotone" size="1rem" />
      </button>
    </div>
    <EditorContent :editor="editor" />
  </div>
</template>

<style scoped>
.rich-text-editor {
  border: 0.0625rem solid var(--border);
  border-radius: var(--radius-md);
  background: var(--surface);
  overflow: hidden;
}
.rich-text-editor__toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.15rem;
  padding: 0.4rem;
  border-bottom: 0.0625rem solid var(--border);
  background: var(--surface-2);
}
.rich-text-editor__toolbar button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.75rem;
  height: 1.75rem;
  padding: 0 0.4rem;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.7rem;
  font-weight: 700;
  cursor: pointer;
}
.rich-text-editor__toolbar button:hover {
  background: var(--surface);
  color: var(--text-primary);
}
.rich-text-editor__toolbar button.active {
  background: var(--tonal-bg);
  color: var(--ember-text);
}
.rich-text-editor__divider {
  width: 0.0625rem;
  margin: 0.15rem 0.2rem;
  background: var(--border);
}
.rich-text-editor :deep(.rich-text-editor__content) {
  min-height: 8rem;
  max-height: 20rem;
  overflow-y: auto;
  padding: 0.6rem 0.75rem;
  font-size: 0.85rem;
  color: var(--text-primary);
}
.rich-text-editor :deep(.rich-text-editor__content:focus) {
  outline: none;
}
.rich-text-editor :deep(.rich-text-editor__content p) {
  margin: 0 0 0.5rem;
}
.rich-text-editor :deep(.rich-text-editor__content h2) {
  font-size: 1.15rem;
  font-weight: 800;
  margin: 0.5rem 0;
}
.rich-text-editor :deep(.rich-text-editor__content h3) {
  font-size: 1rem;
  font-weight: 700;
  margin: 0.5rem 0;
}
.rich-text-editor :deep(.rich-text-editor__content ul),
.rich-text-editor :deep(.rich-text-editor__content ol) {
  padding-left: 1.25rem;
  margin: 0 0 0.5rem;
}
.rich-text-editor :deep(.rich-text-editor__content blockquote) {
  border-left: 0.1875rem solid var(--border);
  padding-left: 0.75rem;
  color: var(--text-secondary);
  margin: 0 0 0.5rem;
}
.rich-text-editor :deep(.rich-text-editor__content a) {
  color: var(--ember-text);
  text-decoration: underline;
}
</style>
