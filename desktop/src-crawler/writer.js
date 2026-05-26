import { writeFileSync, mkdirSync } from "fs";
import { join } from "path";

function slug(name) {
  return name.normalize("NFD").replace(/[̀-ͯ]/g, "")
    .toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function periodoSlug(periodo) {
  if (!periodo) return null;
  return periodo.toLowerCase().replace(/\//g, "-");
}

export function writeEspelho(espelho, outputDir) {
  const serverSlug = slug(espelho.servidor.nome);
  const fileSlug = periodoSlug(espelho.periodo_referencia) ?? espelho.run_id;
  const dir = join(outputDir, "servidores", serverSlug);
  const filePath = join(dir, `espelho-${fileSlug}.json`);
  mkdirSync(dir, { recursive: true });
  writeFileSync(filePath, JSON.stringify(espelho, null, 2), "utf-8");
  return filePath;
}
