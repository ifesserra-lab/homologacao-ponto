<script setup lang="ts">
defineProps<{ items: { label: string; to?: string }[] }>();
</script>

<template>
  <nav class="breadcrumb">
    <template v-for="(item, i) in items" :key="i">
      <span v-if="i > 0" class="sep">›</span>
      <router-link v-if="item.to" :to="item.to" class="crumb crumb--link">{{ item.label }}</router-link>
      <span v-else class="crumb crumb--current">{{ item.label }}</span>
    </template>
  </nav>
</template>

<style scoped>
.breadcrumb { display: flex; align-items: center; gap: 6px; margin-bottom: 1rem; font-size: 13px; }
.sep { color: var(--muted); opacity: 0.5; }
.crumb--link { color: var(--muted); text-decoration: none; }
.crumb--link:hover { color: var(--text); }
.crumb--current { color: var(--text); font-weight: 500; }
</style>
