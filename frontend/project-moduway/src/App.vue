<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import DefaultLayout from '@/layouts/DefaultLayout.vue';

const route = useRoute();

const isLayoutNeeded = computed(() => {
  return route.meta.layout !== 'none';
});
</script>

<template>
  <DefaultLayout v-if="isLayoutNeeded">
    <RouterView />
  </DefaultLayout>
  
  <div v-else>
    <RouterView />
  </div>
</template>
