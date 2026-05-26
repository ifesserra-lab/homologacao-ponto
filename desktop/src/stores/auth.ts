import { defineStore } from "pinia";
import { ref } from "vue";

const SESSION_KEY = "dashboard_auth";

async function sha256(text: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

export const useAuthStore = defineStore("auth", () => {
  const authenticated = ref(false);

  function init() {
    try {
      const raw = sessionStorage.getItem(SESSION_KEY);
      if (raw) authenticated.value = JSON.parse(raw).authenticated === true;
    } catch {
      authenticated.value = false;
    }
  }

  async function login(user: string, password: string, userHash?: string, passwordHash?: string): Promise<boolean> {
    if (!userHash || !passwordHash) {
      authenticated.value = true;
      sessionStorage.setItem(SESSION_KEY, JSON.stringify({ authenticated: true }));
      return true;
    }
    const [uh, ph] = await Promise.all([sha256(user), sha256(password)]);
    if (uh === userHash && ph === passwordHash) {
      authenticated.value = true;
      sessionStorage.setItem(SESSION_KEY, JSON.stringify({ authenticated: true }));
      return true;
    }
    return false;
  }

  function logout() {
    authenticated.value = false;
    sessionStorage.removeItem(SESSION_KEY);
  }

  return { authenticated, init, login, logout };
});
