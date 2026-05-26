import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { listServers, serverDetail, monthDetail, loadAllAfastamentos } from "@/lib/espelhoRepository";
import type { ServidorResume, RawEspelho, AfastamentoPeriodo } from "@/types/dashboard";

const STORAGE_KEY = "ponto_data_dir";
const ENV_DATA_DIR = import.meta.env.VITE_DATA_DIR as string | undefined;

export const useServidoresStore = defineStore("servidores", () => {
  const dataDir = ref<string>(localStorage.getItem(STORAGE_KEY) ?? ENV_DATA_DIR ?? "");
  const servidores = ref<ServidorResume[]>([]);
  const afastamentos = ref<AfastamentoPeriodo[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const isEmpty = computed(() => servidores.value.length === 0);
  const hasDir = computed(() => dataDir.value.trim().length > 0);

  function setDataDir(dir: string) {
    dataDir.value = dir.trim();
    localStorage.setItem(STORAGE_KEY, dataDir.value);
  }

  async function load(dir?: string) {
    if (dir) setDataDir(dir);
    if (!dataDir.value) return;
    loading.value = true;
    error.value = null;
    try {
      const [srvs, afas] = await Promise.all([
        listServers(dataDir.value),
        loadAllAfastamentos(dataDir.value),
      ]);
      servidores.value = srvs;
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

  return { dataDir, servidores, afastamentos, loading, error, isEmpty, hasDir, load, setDataDir, getServidor, getMes };
});
