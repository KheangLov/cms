<script setup lang="ts">
// Renders/edits a `list`-type prop field's items with real inputs instead of the
// old "edit via raw JSON" escape hatch. Self-referencing (recursive) so a nested
// list-of-lists — e.g. Footer's `columns`, each holding its own `links` list —
// works without a hardcoded depth limit.
interface ItemField {
  key: string
  type: string
  label: string
  translatable?: boolean
  itemFields?: ItemField[]
  options?: { title: string; value: string }[]
}

const props = withDefaults(
  defineProps<{
    modelValue: any[]
    itemFields: ItemField[]
    locale?: string
  }>(),
  { locale: 'en' },
)
const emit = defineEmits<{ 'update:modelValue': [value: any[]] }>()

function addItem() {
  const blank: Record<string, any> = {}
  for (const f of props.itemFields) {
    blank[f.key] = f.type === 'list' ? [] : f.type === 'boolean' ? false : f.type === 'select' ? f.options?.[0]?.value ?? '' : ''
  }
  emit('update:modelValue', [...(props.modelValue || []), blank])
}

function removeItem(index: number) {
  const next = [...(props.modelValue || [])]
  next.splice(index, 1)
  emit('update:modelValue', next)
}

function updateItemField(index: number, field: ItemField, value: unknown) {
  const next = [...(props.modelValue || [])]
  const item = { ...next[index] }
  if (field.translatable) {
    item[field.key] = { ...(item[field.key] || {}), [props.locale]: value }
  } else {
    item[field.key] = value
  }
  next[index] = item
  emit('update:modelValue', next)
}

function valueFor(item: Record<string, any>, field: ItemField): string {
  const raw = item?.[field.key]
  if (field.translatable) return raw?.[props.locale] ?? ''
  return raw ?? ''
}
</script>

<template>
  <div class="space-y-2">
    <div v-for="(item, i) in modelValue || []" :key="i" class="bento-card p-3">
      <div class="flex items-center justify-between">
        <span class="text-xs font-bold uppercase" style="color: var(--text-faint)">{{ $t('listEditor.item', { n: i + 1 }) }}</span>
        <button class="bento-icon-btn bento-icon-btn--danger" :title="$t('listEditor.removeItem')" @click="removeItem(i)">
          <Icon name="solar:trash-bin-2-bold-duotone" size="0.9rem" />
        </button>
      </div>
      <div v-for="field in itemFields" :key="field.key" class="mt-2">
        <label v-if="field.type === 'boolean'" class="flex items-center gap-2 text-xs font-semibold">
          <input
            type="checkbox"
            :checked="!!item[field.key]"
            @change="updateItemField(i, field, ($event.target as HTMLInputElement).checked)"
          />
          {{ field.label }}
        </label>
        <template v-else>
          <label class="block text-xs font-semibold">{{ field.label }}</label>
          <ListFieldEditor
            v-if="field.type === 'list'"
            class="mt-1"
            :model-value="item[field.key] || []"
            :item-fields="field.itemFields || []"
            :locale="locale"
            @update:model-value="(v) => updateItemField(i, field, v)"
          />
          <textarea
            v-else-if="field.type === 'textarea'"
            class="bento-input mt-1"
            rows="2"
            :value="valueFor(item, field)"
            @input="updateItemField(i, field, ($event.target as HTMLTextAreaElement).value)"
          />
          <select
            v-else-if="field.type === 'select'"
            class="bento-input mt-1"
            :value="valueFor(item, field)"
            @change="updateItemField(i, field, ($event.target as HTMLSelectElement).value)"
          >
            <option v-for="opt in field.options || []" :key="opt.value" :value="opt.value">{{ opt.title }}</option>
          </select>
          <input
            v-else
            class="bento-input mt-1"
            :value="valueFor(item, field)"
            @input="updateItemField(i, field, ($event.target as HTMLInputElement).value)"
          />
        </template>
      </div>
    </div>
    <v-btn variant="tonal" size="small" block @click="addItem">
      <Icon name="solar:add-circle-bold-duotone" size="1rem" class="mr-1" />
      {{ $t('listEditor.addItem') }}
    </v-btn>
  </div>
</template>
