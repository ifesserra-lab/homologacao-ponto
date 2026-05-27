<script setup lang="ts">
import { ref } from "vue";
import { invoke } from "@tauri-apps/api/core";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";

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
  <div class="login-page">
    <div class="login-card">
      <h1 class="login-title">Gestor de Ponto</h1>
      <p class="login-sub">SIGRH · Acesso restrito</p>
      <form class="login-form" @submit.prevent="submit">
        <div class="field">
          <label for="user">Usuário</label>
          <input id="user" v-model="user" type="text" autocomplete="username" required />
        </div>
        <div class="field">
          <label for="pass">Senha</label>
          <input id="pass" v-model="password" type="password" autocomplete="current-password" required />
        </div>
        <p v-if="error" class="error-msg">Credenciais inválidas.</p>
        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? "Entrando…" : "Entrar" }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: var(--bg); }
.login-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 2rem; width: 100%; max-width: 360px; box-shadow: var(--shadow); }
.login-title { font-size: 20px; font-weight: 600; letter-spacing: -0.02em; margin-bottom: 4px; }
.login-sub { font-size: 13px; color: var(--muted); margin-bottom: 1.5rem; }
.login-form { display: flex; flex-direction: column; gap: 14px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 12px; font-weight: 500; color: var(--text-2); }
.field input { padding: 8px 10px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--bg); color: var(--text); font-size: 14px; outline: none; }
.field input:focus { border-color: var(--blue); box-shadow: 0 0 0 3px var(--focus-ring); }
.error-msg { font-size: 12px; color: var(--red); }
.btn-primary { padding: 9px; background: var(--blue); color: var(--on-accent); border: none; border-radius: var(--radius-sm); font-size: 14px; font-weight: 500; cursor: pointer; transition: opacity 0.15s; }
.btn-primary:hover { opacity: 0.88; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
