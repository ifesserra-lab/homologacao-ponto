import { createRouter, createWebHashHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: "/login", name: "login", component: () => import("@/views/LoginView.vue"), meta: { public: true } },
    { path: "/", name: "home", component: () => import("@/views/ServidorListView.vue") },
    { path: "/indicadores", name: "indicadores", component: () => import("@/views/IndicadoresView.vue") },
    { path: "/crawler", name: "crawler", component: () => import("@/views/CrawlerView.vue") },
    { path: "/servidor/:slug", name: "servidor", component: () => import("@/views/ServidorDetailView.vue") },
    { path: "/servidor/:slug/:periodo", name: "periodo", component: () => import("@/views/ServidorPeriodoView.vue") },
  ],
});

router.beforeEach((to) => {
  const auth = useAuthStore();
  if (!to.meta.public && !auth.authenticated) {
    return { name: "login", query: { redirect: to.fullPath } };
  }
});

export default router;
