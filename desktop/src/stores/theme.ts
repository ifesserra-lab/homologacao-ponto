import { defineStore } from "pinia";
import { ref } from "vue";

type Theme = "light" | "dark";

export const useThemeStore = defineStore("theme", () => {
  const theme = ref<Theme>("light");

  function init() {
    const stored = localStorage.getItem("dashboard_theme") as Theme | null;
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    theme.value = stored === "dark" || stored === "light" ? stored : prefersDark ? "dark" : "light";
    apply();
  }

  function toggle() {
    theme.value = theme.value === "dark" ? "light" : "dark";
    localStorage.setItem("dashboard_theme", theme.value);
    apply();
  }

  function apply() {
    document.documentElement.dataset.theme = theme.value;
  }

  return { theme, init, toggle };
});
