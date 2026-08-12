<script setup lang="ts">
import { Swiper, SwiperSlide } from 'swiper/vue'
import 'swiper/css'

interface Props {
  block: { props: Record<string, any> }
  locale?: string
}
const props = defineProps<Props>()

function caption(slide: Record<string, any>): string {
  const value = slide.caption
  if (value && typeof value === 'object') {
    return value[props.locale || 'en'] ?? value.en ?? ''
  }
  return value ?? ''
}

const slides = computed<Array<Record<string, any>>>(() => props.block.props.slides || [])
</script>

<template>
  <section class="px-6 py-8">
    <Swiper :space-between="16" :slides-per-view="1">
      <SwiperSlide v-for="(slide, i) in slides" :key="i">
        <img
          v-if="slide.imageUrl"
          :src="slide.imageUrl"
          class="w-full rounded-lg object-cover"
          :alt="caption(slide)"
        />
        <p v-if="caption(slide)" class="mt-2 text-center text-sm">{{ caption(slide) }}</p>
      </SwiperSlide>
    </Swiper>
  </section>
</template>
