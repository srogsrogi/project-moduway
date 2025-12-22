<template>
  <div class="layout-wrapper">
    <AppHeader />
    <main>
      <slot />
    </main>
    <AppFooter />
    <ComparisonBar />
  </div>
</template>

<script setup>
import AppHeader from '@/components/common/AppHeader.vue';
import AppFooter from '@/components/common/AppFooter.vue';
import ComparisonBar from '@/components/comparison/ComparisonBar.vue';
</script>

<style scoped>
.layout-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
main {
  flex: 1;
}
</style>
