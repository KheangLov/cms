<script setup lang="ts">
const { confirmState, resolve } = useConfirmDialog()
</script>

<template>
  <v-dialog v-model="confirmState.open" max-width="420" @update:model-value="(v) => !v && resolve(false)">
    <v-card>
      <div class="flex items-start gap-3 p-5 pb-3">
        <span
          class="bento-tile__icon"
          :class="confirmState.danger ? 'bento-tile__icon--error' : 'bento-tile__icon--info'"
          style="width: 2.5rem; height: 2.5rem; font-size: 1.3rem"
        >
          <Icon :name="confirmState.danger ? 'solar:trash-bin-2-bold-duotone' : 'solar:question-circle-bold-duotone'" />
        </span>
        <div class="pt-0.5">
          <h2 class="font-bold">{{ confirmState.title }}</h2>
          <p class="mt-1 text-sm" style="color: var(--text-secondary)">{{ confirmState.message }}</p>
        </div>
      </div>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="resolve(false)">{{ confirmState.cancelLabel }}</v-btn>
        <v-btn :color="confirmState.danger ? 'error' : 'primary'" variant="elevated" @click="resolve(true)">
          {{ confirmState.confirmLabel }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
