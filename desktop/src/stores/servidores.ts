import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { invoke } from "@tauri-apps/api/core";
import { listServers, serverDetail, monthDetail, loadAllAfastamentos } from "@/lib/espelhoRepository";
import type { ServidorResume, RawEspelho, AfastamentoPeriodo } from "@/types/dashboard";

export const useServidoresStore = defineStore("servidores", () => {
  const dataDir = ref<string>(import.meta.env.VITE_DATA_DIR ?? "");
  const servidores = ref<ServidorResume[]>([]);
  const afastamentos = ref<AfastamentoPeriodo[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const isEmpty = computed(() => servidores.value.length === 0);

  async function load() {
    loading.value = true;
    error.value = null;
    try {
      dataDir.value = await invoke<string>("resolve_data_dir");
      const [srvs, afas] = await Promise.all([
        listServers(dataDir.value),
        loadAllAfastamentos(dataDir.value),
      ]);
      servidores.value = srvs.sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
      afastamentos.value = afas;
    } catch (e) {
      error.value = String(e);
    } finally {
      loading.value = false;
    }
  }

  async function getServidor(slug: string): Promise<ServidorResume | undefined> {
    const cached = servidores.value.find((s) => s.slug === slug);
    if (cached) return cached;
    return serverDetail(slug, dataDir.value);
  }

  async function getMes(slug: string, periodo: string): Promise<RawEspelho | undefined> {
    return monthDetail(slug, periodo, dataDir.value);
  }

  return { dataDir, servidores, afastamentos, loading, error, isEmpty, load, getServidor, getMes };
});
