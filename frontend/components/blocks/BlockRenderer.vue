<script setup lang="ts">
import CalloutBlock from './CalloutBlock.vue'
import CardsBlock from './CardsBlock.vue'
import ColumnsBlock from './ColumnsBlock.vue'
import ContactFormBlock from './ContactFormBlock.vue'
import FeatureGridBlock from './FeatureGridBlock.vue'
import FooterBlock from './FooterBlock.vue'
import HeroBlock from './HeroBlock.vue'
import MapBlock from './MapBlock.vue'
import NavbarBlock from './NavbarBlock.vue'
import PostsBlock from './PostsBlock.vue'
import QuizBlock from './QuizBlock.vue'
import SurveyBlock from './SurveyBlock.vue'
import SwiperBlock from './SwiperBlock.vue'
import TextSectionBlock from './TextSectionBlock.vue'

interface BlockNode {
  id: number
  block_type: { slug: string; name: string }
  order: number
  props: Record<string, any>
  children: BlockNode[]
}

defineProps<{
  blocks: BlockNode[]
  locale?: string
}>()

// CMS_BUILD_PROMPT.md §5.2 — the same map (and the same components) render both
// the builder canvas and the public page. Adding a block type = a registry row
// (apps/blocks migrations) + a Vue component + one line here.
const componentMap: Record<string, unknown> = {
  hero: HeroBlock,
  'text-section': TextSectionBlock,
  swiper: SwiperBlock,
  columns: ColumnsBlock,
  posts: PostsBlock,
  navbar: NavbarBlock,
  footer: FooterBlock,
  'feature-grid': FeatureGridBlock,
  callout: CalloutBlock,
  cards: CardsBlock,
  'contact-form': ContactFormBlock,
  map: MapBlock,
  'quiz-embed': QuizBlock,
  'survey-embed': SurveyBlock,
}
</script>

<template>
  <template v-for="block in blocks" :key="block.id">
    <component
      :is="componentMap[block.block_type.slug]"
      v-if="componentMap[block.block_type.slug]"
      :block="block"
      :locale="locale || 'en'"
    />
    <div v-else class="rounded border border-dashed border-gray-300 p-4 text-sm text-gray-400">
      {{ $t('blockRenderer.unknownBlockType', { slug: block.block_type.slug }) }}
    </div>
  </template>
</template>
