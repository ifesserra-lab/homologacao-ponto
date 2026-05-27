<script setup lang="ts">
import { ref } from "vue";
import { invoke } from "@tauri-apps/api/core";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import ThemeToggle from "@/components/ThemeToggle.vue";

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();

const user = ref("");
const password = ref("");
const error = ref(false);
const loading = ref(false);

async function submit() {
  loading.value = true;
  error.value = false;
  const { usuario_hash, senha_hash } = await invoke<{ usuario_hash: string; senha_hash: string }>("get_app_auth");
  const ok = await auth.login(user.value, password.value, usuario_hash || undefined, senha_hash || undefined);
  loading.value = false;
  if (ok) {
    const redirect = (route.query.redirect as string) ?? "/";
    router.push(redirect);
  } else {
    error.value = true;
  }
}
</script>

<template>
  <ThemeToggle class="login-theme" />
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">
        <svg width="64" height="64" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
          <rect width="512" height="512" rx="112" fill="#0F7B6C"/>
          <rect x="76" y="130" width="360" height="300" rx="36" fill="white" opacity="0.15"/>
          <rect x="76" y="130" width="360" height="300" rx="36" fill="none" stroke="white" stroke-width="10" opacity="0.4"/>
          <rect x="76" y="130" width="360" height="96" rx="36" fill="white" opacity="0.92"/>
          <rect x="76" y="190" width="360" height="36" fill="white" opacity="0.92"/>
          <rect x="168" y="88" width="32" height="86" rx="16" fill="white"/>
          <rect x="312" y="88" width="32" height="86" rx="16" fill="white"/>
          <polyline points="158,310 224,376 354,246" fill="none" stroke="white" stroke-width="48" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <h1 class="login-title">Gestor de Ponto</h1>
      <p class="login-subtitle">SIGRH · Acesso restrito</p>
      <form class="login-form" @submit.prevent="submit">
        <div class="login-field">
          <label for="user">Usuário</label>
          <input id="user" v-model="user" type="text" autocomplete="username" placeholder="seu usuário" required />
        </div>
        <div class="login-field">
          <label for="pass">Senha</label>
          <input id="pass" v-model="password" type="password" autocomplete="current-password" placeholder="••••••••" required />
        </div>
        <div v-if="error" class="login-error">Credenciais inválidas.</div>
        <button type="submit" class="login-btn" :disabled="loading">
          {{ loading ? "Entrando…" : "Entrar" }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-logo { margin-bottom: 1.25rem; display: flex; justify-content: center; }
.login-title, .login-subtitle { text-align: center; }
</style>
