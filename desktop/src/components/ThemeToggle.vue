<script setup lang="ts">
import { useThemeStore } from "@/stores/theme";
const theme = useThemeStore();
</script>

<template>
  <button class="theme-toggle" type="button" :aria-label="`Tema ${theme.theme}`" @click="theme.toggle">
    <svg v-if="theme.theme === 'light'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
    </svg>
    <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
    </svg>
  </button>
</template>

<style scoped>
.theme-toggle {
  display: flex; align-items: center; justify-content: center;
  width: 32px; height: 32px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--muted); cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}
.theme-toggle:hover { color: var(--text); border-color: var(--border-mid); }
</style>
