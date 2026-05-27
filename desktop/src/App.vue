<script setup lang="ts">
import { onMounted } from "vue";
import { useThemeStore } from "@/stores/theme";
import { useAuthStore } from "@/stores/auth";
import CrawlerLogModal from "@/components/CrawlerLogModal.vue";

const theme = useThemeStore();
const auth = useAuthStore();

onMounted(() => {
  theme.init();
  auth.init();
});
</script>

<template>
  <router-view />
  <CrawlerLogModal />
</template>
